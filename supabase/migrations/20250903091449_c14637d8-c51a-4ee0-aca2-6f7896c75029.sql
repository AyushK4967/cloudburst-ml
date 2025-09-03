-- Add Jupyter connection details to notebooks table
ALTER TABLE public.notebooks 
ADD COLUMN jupyter_url TEXT,
ADD COLUMN jupyter_port INTEGER,
ADD COLUMN jupyter_token TEXT,
ADD COLUMN container_id TEXT;