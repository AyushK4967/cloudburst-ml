import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { 
  Rocket, 
  Square,
  Trash2,
  ExternalLink,
  Activity,
  Clock, 
  BarChart3,
  Plus,
  RefreshCw,
  Code
} from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';
import { useAuth } from '@/components/auth/AuthProvider';

interface Model {
  id: string;
  name: string;
  description?: string;
  endpoint: string;
  status: 'deployed' | 'deploying' | 'stopped' | 'failed';
  framework: string;
  created_at: string;
  daily_calls: number;
  avg_latency: number;
  user_id: string;
}

export const ModelManager = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [deployDialogOpen, setDeployDialogOpen] = useState(false);
  const [newModel, setNewModel] = useState({ 
    name: '', 
    description: '', 
    framework: 'pytorch',
    model_file: null as File | null
  });
  const { user } = useAuth();

  const fetchModels = async () => {
    if (!user) return;
    
    try {
      const { data, error } = await supabase
        .from('deployed_models')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;
      setModels(data || []);
    } catch (error) {
      console.error('Error fetching models:', error);
      toast.error('Failed to load models');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, [user]);

  const deployModel = async () => {
    if (!user || !newModel.name.trim()) return;

    try {
      const endpoint = `api/v1/${newModel.name.toLowerCase().replace(/\s+/g, '-')}`;
      
      const { data, error } = await supabase
        .from('deployed_models')
        .insert({
          name: newModel.name.trim(),
          description: newModel.description.trim(),
          endpoint,
          framework: newModel.framework,
          user_id: user.id,
          status: 'deploying'
        })
        .select()
        .single();

      if (error) throw error;
      
      setModels(prev => [data, ...prev]);
      setDeployDialogOpen(false);
      setNewModel({ name: '', description: '', framework: 'pytorch', model_file: null });
      toast.success('Model deployment started');
      
      // Simulate deployment process
      setTimeout(() => {
        setModels(prev => 
          prev.map(model => model.id === data.id ? { ...model, status: 'deployed' } : model)
        );
        toast.success('Model deployed successfully');
      }, 5000);
    } catch (error) {
      console.error('Error deploying model:', error);
      toast.error('Failed to deploy model');
    }
  };

  const toggleModel = async (model: Model) => {
    const newStatus = model.status === 'deployed' ? 'stopped' : 'deploying';
    
    try {
      const { error } = await supabase
        .from('deployed_models')
        .update({ status: newStatus })
        .eq('id', model.id);

      if (error) throw error;
      
      setModels(prev => 
        prev.map(m => m.id === model.id ? { ...m, status: newStatus } : m)
      );

      setTimeout(() => {
        const finalStatus = newStatus === 'deploying' ? 'deployed' : 'stopped';
        setModels(prev => 
          prev.map(m => m.id === model.id ? { ...m, status: finalStatus } : m)
        );
      }, 3000);
    } catch (error) {
      console.error('Error updating model:', error);
      toast.error('Failed to update model');
    }
  };

  const deleteModel = async (modelId: string) => {
    try {
      const { error } = await supabase
        .from('deployed_models')
        .delete()
        .eq('id', modelId);

      if (error) throw error;
      
      setModels(prev => prev.filter(m => m.id !== modelId));
      toast.success('Model deleted');
    } catch (error) {
      console.error('Error deleting model:', error);
      toast.error('Failed to delete model');
    }
  };

  const openAPI = (model: Model) => {
    if (model.status !== 'deployed') {
      toast.error('Model must be deployed to access API');
      return;
    }
    // Show API documentation
    navigator.clipboard.writeText(`https://api.mlcloud.dev/${model.endpoint}`);
    toast.success('API endpoint copied to clipboard');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'deployed': return 'default';
      case 'deploying': return 'secondary';
      case 'failed': return 'destructive';
      default: return 'outline';
    }
  };

  if (!user) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <p>Please sign in to manage your models</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Deployed Models</h2>
          <p className="text-muted-foreground">ML models deployed as REST APIs</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchModels}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Dialog open={deployDialogOpen} onOpenChange={setDeployDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Deploy Model
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Deploy New Model</DialogTitle>
                <DialogDescription>
                  Deploy your trained model as a REST API endpoint
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="model-name">Model Name</Label>
                  <Input
                    id="model-name"
                    placeholder="My Awesome Model"
                    value={newModel.name}
                    onChange={(e) => setNewModel(prev => ({ ...prev, name: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="model-description">Description (Optional)</Label>
                  <Textarea
                    id="model-description"
                    placeholder="What does this model do?"
                    value={newModel.description}
                    onChange={(e) => setNewModel(prev => ({ ...prev, description: e.target.value }))}
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="framework">Framework</Label>
                  <Select
                    value={newModel.framework}
                    onValueChange={(value) => setNewModel(prev => ({ ...prev, framework: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pytorch">PyTorch</SelectItem>
                      <SelectItem value="tensorflow">TensorFlow</SelectItem>
                      <SelectItem value="scikit-learn">Scikit-learn</SelectItem>
                      <SelectItem value="huggingface">HuggingFace</SelectItem>
                      <SelectItem value="onnx">ONNX</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="model-file">Model File</Label>
                  <Input
                    id="model-file"
                    type="file"
                    accept=".pkl,.pt,.pth,.h5,.joblib,.onnx,.pb"
                    onChange={(e) => setNewModel(prev => ({ 
                      ...prev, 
                      model_file: e.target.files?.[0] || null 
                    }))}
                  />
                  <p className="text-xs text-muted-foreground">
                    Supported formats: .pkl, .pt, .pth, .h5, .joblib, .onnx, .pb
                  </p>
                </div>
                <Button onClick={deployModel} className="w-full" disabled={!newModel.name.trim()}>
                  Deploy Model
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4">
          {[1, 2, 3].map(i => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="animate-pulse space-y-4">
                  <div className="h-4 bg-muted rounded w-1/3"></div>
                  <div className="h-3 bg-muted rounded w-1/2"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : models.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Rocket className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No models deployed</h3>
            <p className="text-muted-foreground mb-4">
              Deploy your first model to start serving predictions
            </p>
            <Button onClick={() => setDeployDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Deploy First Model
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {models.map((model) => (
            <Card key={model.id}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-semibold text-lg">{model.name}</h3>
                      <Badge variant={getStatusColor(model.status)}>
                        {model.status}
                      </Badge>
                    </div>
                    {model.description && (
                      <p className="text-sm text-muted-foreground mb-2">{model.description}</p>
                    )}
                    <p className="text-sm font-mono text-muted-foreground mb-3">
                      {model.endpoint}
                    </p>
                    <div className="flex items-center space-x-6 text-sm text-muted-foreground">
                      <div className="flex items-center space-x-1">
                        <BarChart3 className="h-4 w-4" />
                        <span>{model.daily_calls} calls today</span>
                      </div>
                      <Separator orientation="vertical" className="h-4" />
                      <div className="flex items-center space-x-1">
                        <Activity className="h-4 w-4" />
                        <span>Avg: {model.avg_latency}ms</span>
                      </div>
                      <Separator orientation="vertical" className="h-4" />
                      <div className="flex items-center space-x-1">
                        <Code className="h-4 w-4" />
                        <span>{model.framework}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {model.status === 'deployed' && (
                      <Button size="sm" variant="outline" onClick={() => openAPI(model)}>
                        <ExternalLink className="h-4 w-4 mr-1" />
                        API
                      </Button>
                    )}
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => toggleModel(model)}
                      disabled={model.status === 'deploying'}
                    >
                      {model.status === 'deployed' ? (
                        <Square className="h-4 w-4" />
                      ) : (
                        <Rocket className="h-4 w-4" />
                      )}
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => deleteModel(model.id)}
                      disabled={model.status === 'deployed'}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};