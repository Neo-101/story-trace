from typing import List, Dict, Tuple
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from core.db.models import Chapter, PlotSegment, PlotArc, AnalysisRun

class PlotSegmenter:
    """
    启发式剧情分段器 & 聚合器 (Arc)
    """
    def __init__(self, session: Session):
        self.session = session

    def analyze_arcs(self, run_id: int) -> List[PlotArc]:
        """
        基于已生成的 Segments，聚合为 Arcs
        """
        # 1. Fetch Segments
        segments = self.session.exec(
            select(PlotSegment)
            .where(PlotSegment.run_id == run_id)
            .order_by(PlotSegment.start_chapter_index)
        ).all()
        
        if not segments:
            return []
            
        # 2. Heuristic Aggregation
        # Strategy: Group 3-5 segments into an Arc, or based on Volume boundaries.
        # Ideally, we detect "Intensity Cycles" (Low -> High -> Low -> End of Arc).
        
        arcs: List[PlotArc] = []
        current_arc_segments: List[PlotSegment] = []
        
        # Helper
        def finalize_arc():
            if not current_arc_segments: return
            
            start = current_arc_segments[0].start_chapter_index
            end = current_arc_segments[-1].end_chapter_index
            vol = current_arc_segments[0].volume_title
            
            arcs.append(PlotArc(
                run_id=run_id,
                volume_title=vol,
                title=f"Arc {len(arcs) + 1}", # Placeholder
                synopsis="",
                start_chapter_index=start,
                end_chapter_index=end
            ))
            current_arc_segments.clear()

        for seg in segments:
            # Check for Volume Change
            if current_arc_segments:
                if seg.volume_title != current_arc_segments[0].volume_title:
                    finalize_arc()
            
            current_arc_segments.append(seg)
            
            # Check for Intensity Cycle Completion
            # If current Arc has > 3 segments, and we just finished a "High" intensity segment and dropped to "Low"
            # Or simply every 4-6 segments.
            # Let's use a count-based heuristic for now (e.g. 5 segments max per arc)
            # OR better: Cumulative chapter count > 20
            
            chapter_count = sum((s.end_chapter_index - s.start_chapter_index + 1) for s in current_arc_segments)
            
            if chapter_count >= 20: # An arc usually has 20-40 chapters
                finalize_arc()
                
        finalize_arc()
        
        # 3. Persist
        try:
            # Clear old arcs
            existing = self.session.exec(select(PlotArc).where(PlotArc.run_id == run_id)).all()
            for e in existing:
                self.session.delete(e)
            self.session.commit()
            
            for arc in arcs:
                self.session.add(arc)
            self.session.commit()
            
            print(f"Successfully generated {len(arcs)} arcs for run {run_id}.")
            return arcs
        except Exception as e:
            print(f"Error persisting arcs: {e}")
            self.session.rollback()
            return []

    def analyze_run(self, run_id: int) -> List[PlotSegment]:
        """
        对指定 Run 的所有章节进行分段分析并保存结果
        """
        # 1. Fetch chapters sorted by index with eager loading
        try:
            chapters = self.session.exec(
                select(Chapter)
                .where(Chapter.run_id == run_id)
                .order_by(Chapter.chapter_index)
                .options(selectinload(Chapter.entities), selectinload(Chapter.relationships))
            ).all()
        except Exception as e:
            print(f"Error fetching chapters for run {run_id}: {e}")
            return []
        
        if not chapters:
            print(f"No chapters found for run {run_id}, skipping segmentation.")
            return []
            
        # 2. Group by Volume
        volumes: Dict[str, List[Chapter]] = {}
        for chap in chapters:
            vol = chap.volume_title or "未分卷"
            if vol not in volumes:
                volumes[vol] = []
            volumes[vol].append(chap)
            
        all_segments = []
        
        # 3. Calculate Global Intensity Thresholds (Percentiles)
        # We need this to determine Low/Medium/High
        all_scores = []
        for chap in chapters:
            score = self._calculate_intensity(chap)
            all_scores.append(score)
            
        all_scores.sort()
        if not all_scores:
            p33, p66 = 0, 0
        else:
            p33 = all_scores[int(len(all_scores) * 0.33)]
            p66 = all_scores[int(len(all_scores) * 0.66)]
            
        # 4. Process each volume
        for vol_title, vol_chapters in volumes.items():
            if len(vol_chapters) <= 5:
                # Too short, single segment
                seg = self._create_segment(run_id, vol_title, vol_chapters)
                all_segments.append(seg)
                continue
                
            # Heuristic Segmentation
            current_chunk: List[Chapter] = []
            if not vol_chapters: continue
            
            current_level = self._get_level(self._calculate_intensity(vol_chapters[0]), p33, p66)
            
            for chap in vol_chapters:
                score = self._calculate_intensity(chap)
                level = self._get_level(score, p33, p66)
                
                # Logic: Split if drastic change (High <-> Low) AND current chunk length >= 3
                # OR if current chunk length >= 8 (force split)
                
                is_drastic = (current_level == 'Low' and level == 'High') or \
                             (current_level == 'High' and level == 'Low')
                             
                chunk_len = len(current_chunk)
                should_split = False
                
                if chunk_len >= 8:
                    should_split = True
                elif chunk_len >= 3 and is_drastic:
                    should_split = True
                    
                if should_split and current_chunk:
                    # Finalize current segment
                    seg = self._create_segment(run_id, vol_title, current_chunk)
                    all_segments.append(seg)
                    current_chunk = []
                    current_level = level # Update level to new start
                
                current_chunk.append(chap)
                
            # Finalize last chunk
            if current_chunk:
                seg = self._create_segment(run_id, vol_title, current_chunk)
                all_segments.append(seg)
                
        # 5. Persist to DB
        try:
            # Delete existing segments for this run
            existing = self.session.exec(select(PlotSegment).where(PlotSegment.run_id == run_id)).all()
            for e in existing:
                self.session.delete(e)
            self.session.commit() # Commit deletion first
            
            # Add new segments
            for seg in all_segments:
                self.session.add(seg)
                
            self.session.commit()
            print(f"Successfully generated {len(all_segments)} segments for run {run_id}.")
            return all_segments
        except Exception as e:
            print(f"Error persisting segments: {e}")
            self.session.rollback()
            return []

    def _calculate_intensity(self, chapter: Chapter) -> float:
        # Score = entity_count * 1.5 + relationship_count * 3.0
        # Note: chapter.entities is a list of Entity objects
        # chapter.relationships is a list of StoryRelationship objects
        try:
            e_count = len(chapter.entities)
            r_count = len(chapter.relationships)
            return (e_count * 1.5) + (r_count * 3.0)
        except Exception:
            return 0.0

    def _get_level(self, score: float, p33: float, p66: float) -> str:
        if score >= p66: return 'High'
        if score >= p33: return 'Medium'
        return 'Low'

    def _create_segment(self, run_id: int, vol_title: str, chapters: List[Chapter]) -> PlotSegment:
        # Calculate avg intensity
        total = sum(self._calculate_intensity(c) for c in chapters)
        avg = total / len(chapters) if chapters else 0
        
        return PlotSegment(
            run_id=run_id,
            volume_title=vol_title,
            title=f"Segment {chapters[0].chapter_index}-{chapters[-1].chapter_index}", # Placeholder
            synopsis="",
            start_chapter_index=chapters[0].chapter_index,
            end_chapter_index=chapters[-1].chapter_index,
            avg_intensity=avg
        )
