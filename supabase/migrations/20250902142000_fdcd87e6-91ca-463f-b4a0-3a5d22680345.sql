-- Create notebooks table for Jupyter notebook management
CREATE TABLE public.notebooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  gpu_type TEXT DEFAULT 'T4',
  status TEXT DEFAULT 'stopped' CHECK (status IN ('running', 'stopped', 'starting', 'stopping')),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  runtime_minutes INTEGER DEFAULT 0
);

-- Create deployed models table for model deployment management
CREATE TABLE public.deployed_models (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  endpoint TEXT UNIQUE NOT NULL,
  framework TEXT DEFAULT 'pytorch',
  status TEXT DEFAULT 'stopped' CHECK (status IN ('deployed', 'deploying', 'stopped', 'failed')),
  daily_calls INTEGER DEFAULT 0,
  avg_latency INTEGER DEFAULT 100,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create usage tracking table for billing
CREATE TABLE public.usage_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  resource_type TEXT NOT NULL, -- 'notebook', 'model', 'api_call'
  resource_id UUID,
  usage_amount DECIMAL(10,4) DEFAULT 0, -- hours for GPU, count for API calls
  cost_amount DECIMAL(10,4) DEFAULT 0, -- cost in dollars
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.notebooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deployed_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;

-- Create policies for notebooks
CREATE POLICY "Users can view their own notebooks" ON public.notebooks
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own notebooks" ON public.notebooks
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own notebooks" ON public.notebooks
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own notebooks" ON public.notebooks
  FOR DELETE USING (auth.uid() = user_id);

-- Create policies for deployed models
CREATE POLICY "Users can view their own models" ON public.deployed_models
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own models" ON public.deployed_models
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own models" ON public.deployed_models
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own models" ON public.deployed_models
  FOR DELETE USING (auth.uid() = user_id);

-- Create policies for usage logs
CREATE POLICY "Users can view their own usage" ON public.usage_logs
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own usage" ON public.usage_logs
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at columns
CREATE TRIGGER update_notebooks_updated_at
    BEFORE UPDATE ON public.notebooks
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_deployed_models_updated_at
    BEFORE UPDATE ON public.deployed_models
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Create indexes for better performance
CREATE INDEX idx_notebooks_user_id ON public.notebooks(user_id);
CREATE INDEX idx_notebooks_status ON public.notebooks(status);
CREATE INDEX idx_deployed_models_user_id ON public.deployed_models(user_id);
CREATE INDEX idx_deployed_models_status ON public.deployed_models(status);
CREATE INDEX idx_usage_logs_user_id ON public.usage_logs(user_id);
CREATE INDEX idx_usage_logs_created_at ON public.usage_logs(created_at);