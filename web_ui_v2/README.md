# StoryTrace V2 Frontend

This is the new, modern frontend for StoryTrace, built with:
- **Vite**
- **Vue 3 + TypeScript**
- **Tailwind CSS**
- **Pinia**

## Setup

1.  Install dependencies:
    ```bash
    npm install
    ```

2.  Start the development server:
    ```bash
    npm run dev
    ```

3.  Make sure the backend is running on port 8000:
    ```bash
    # In the project root
    python web_ui/server.py
    # OR
    python main.py --server
    ```

## Features
- **Overview Mode**: Responsive grid layout with auto-scroll to selected chapter.
- **Focus Mode**: Immersive reader with entity highlights.
- **Graph Mode**: (Coming Soon) Interactive relationship graph.
