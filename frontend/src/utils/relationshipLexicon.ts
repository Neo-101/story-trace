export const RELATIONSHIP_LEXICON: Record<string, { label: string, score: number, keywords: string[] }> = {
    // --- 强正向 (Strong Positive) ---
    "Lifebound": {
        label: "生死之交",
        score: 10.0, // Significantly increased to represent defining moments
        keywords: ["救命", "牺牲", "复活", "挡刀", "拼死", "誓言", "营救", "救助", "解救"]
    },
    "Lover": {
        label: "恋人",
        score: 8.0,
        keywords: ["亲吻", "求婚", "约会", "表白", "爱抚", "同居"]
    },
    
    // --- 中正向 (Medium Positive) ---
    "Ally": {
        label: "盟友",
        score: 3.0,
        keywords: ["结盟", "合作", "并肩", "支援", "掩护", "共谋", "加入", "联手", "组队", "团队", "队友", "入伙"]
    },
    "Friend": {
        label: "朋友",
        score: 2.0,
        keywords: ["安慰", "拥抱", "聚会", "赠送", "玩笑", "关心", "叙旧", "招待", "闲聊", "寒暄", "请客", "聚餐", "吃饭"]
    },
    "Master": {
        label: "效忠", // A效忠B
        score: 4.0,
        keywords: ["服从", "跪拜", "宣誓", "追随", "护卫", "效忠", "听命"]
    },

    // --- 弱正向/功能性 (Weak Positive / Functional) ---
    "Colleague": {
        label: "同僚",
        score: 0.5,
        keywords: ["汇报", "商议", "通知", "交接", "引荐", "共事", "搭档"]
    },
    "Owner": {
        label: "持有", // 人对物
        score: 0.1,
        keywords: ["使用", "驾驶", "佩戴", "装备", "购买", "修理", "改造", "唤醒", "启动"]
    },

    // --- 弱负向 (Weak Negative) ---
    "Stranger": {
        label: "陌生",
        score: -0.2, // Slightly stronger than Owner (0.1) to prioritize distance
        keywords: ["打量", "无视", "路过", "偶遇", "擦肩", "询问"]
    },
    "Dislike": {
        label: "嫌隙",
        score: -1.2, // Stronger than Friend (1.0) to prioritize conflict
        keywords: ["争吵", "嘲讽", "拒绝", "怀疑", "不悦", "冷落", "警告", "厌恶", "反感", "讽刺", "斥责", "拉黑", "断交"]
    },

    // --- 中负向 (Medium Negative) ---
    "Enemy": {
        label: "敌人",
        score: -3.0,
        keywords: ["攻击", "对峙", "伏击", "追杀", "囚禁", "审讯", "威胁", "伤害", "战斗", "交手", "动手", "冲突", "算计", "偷袭", "背叛", "暗算", "阻拦", "击退", "包围", "殴打", "暴打", "揍", "出卖"]
    },
    
    // --- 强负向 (Strong Negative) ---
    "Nemesis": {
        label: "死敌",
        score: -10.0,
        keywords: ["杀害", "处决", "毁灭", "虐待", "血仇", "同归于尽", "死斗", "绝杀", "斩首", "屠杀", "碎尸"]
    }
};

// 辅助函数：根据关键词匹配关系类型
export function matchRelationType(action: string): { type: string, score: number } | null {
    if (!action) return null;
    
    for (const [type, data] of Object.entries(RELATIONSHIP_LEXICON)) {
        if (data.keywords.some(k => action.includes(k))) {
            return { type, score: data.score };
        }
    }
    return null;
}
