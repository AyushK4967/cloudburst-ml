-- Create secure token storage table
CREATE TABLE public.notebook_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  notebook_id UUID NOT NULL REFERENCES public.notebooks(id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  encrypted_token TEXT NOT NULL,
  token_hash TEXT NOT NULL,
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (now() + interval '24 hours'),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(notebook_id)
);

-- Enable RLS on notebook_tokens
ALTER TABLE public.notebook_tokens ENABLE ROW LEVEL SECURITY;

-- Create policies for notebook_tokens (very restrictive)
CREATE POLICY "Users can only access their notebook tokens through functions" 
ON public.notebook_tokens 
FOR ALL 
USING (false); -- Block direct access entirely

-- Create security definer function to securely handle tokens
CREATE OR REPLACE FUNCTION public.create_notebook_token(
  p_notebook_id UUID,
  p_encrypted_token TEXT,
  p_token_hash TEXT
) RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_token_id UUID;
  v_user_id UUID;
BEGIN
  -- Get current user
  v_user_id := auth.uid();
  
  -- Verify user owns the notebook
  IF NOT EXISTS (
    SELECT 1 FROM public.notebooks 
    WHERE id = p_notebook_id AND user_id = v_user_id
  ) THEN
    RAISE EXCEPTION 'Access denied: notebook not found or not owned by user';
  END IF;
  
  -- Insert or update token
  INSERT INTO public.notebook_tokens (notebook_id, user_id, encrypted_token, token_hash)
  VALUES (p_notebook_id, v_user_id, p_encrypted_token, p_token_hash)
  ON CONFLICT (notebook_id) 
  DO UPDATE SET 
    encrypted_token = EXCLUDED.encrypted_token,
    token_hash = EXCLUDED.token_hash,
    expires_at = now() + interval '24 hours'
  RETURNING id INTO v_token_id;
  
  RETURN v_token_id;
END;
$$;

-- Create function to securely retrieve tokens
CREATE OR REPLACE FUNCTION public.get_notebook_token(p_notebook_id UUID)
RETURNS TABLE(encrypted_token TEXT, expires_at TIMESTAMP WITH TIME ZONE)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user_id UUID;
BEGIN
  -- Get current user
  v_user_id := auth.uid();
  
  -- Verify user owns the notebook and token hasn't expired
  RETURN QUERY
  SELECT nt.encrypted_token, nt.expires_at
  FROM public.notebook_tokens nt
  JOIN public.notebooks n ON n.id = nt.notebook_id
  WHERE nt.notebook_id = p_notebook_id 
    AND n.user_id = v_user_id
    AND nt.expires_at > now();
END;
$$;

-- Create function to clean up expired tokens
CREATE OR REPLACE FUNCTION public.cleanup_expired_tokens()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_deleted_count INTEGER;
BEGIN
  DELETE FROM public.notebook_tokens 
  WHERE expires_at < now();
  
  GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
  RETURN v_deleted_count;
END;
$$;

-- Remove jupyter_token from notebooks table (security improvement)
ALTER TABLE public.notebooks 
DROP COLUMN IF EXISTS jupyter_token;

-- Add trigger to clean up tokens when notebook is deleted
CREATE OR REPLACE FUNCTION public.cleanup_notebook_tokens()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  DELETE FROM public.notebook_tokens WHERE notebook_id = OLD.id;
  RETURN OLD;
END;
$$;

CREATE TRIGGER cleanup_notebook_tokens_trigger
  BEFORE DELETE ON public.notebooks
  FOR EACH ROW
  EXECUTE FUNCTION public.cleanup_notebook_tokens();