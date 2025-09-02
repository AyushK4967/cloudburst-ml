import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { 
  Play, 
  Square,
  Trash2,
  ExternalLink,
  Cpu, 
  Clock, 
  Monitor,
  Plus,
  RefreshCw
} from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';
import { useAuth } from '@/components/auth/AuthProvider';
import type { Database } from '@/integrations/supabase/types';

type Notebook = Database['public']['Tables']['notebooks']['Row'];

export const NotebookManager = () => {
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newNotebook, setNewNotebook] = useState({ name: '', gpu_type: 'T4' });
  const { user } = useAuth();

  const fetchNotebooks = async () => {
    if (!user) return;
    
    try {
      const { data, error } = await supabase
        .from('notebooks')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;
      setNotebooks(data || []);
    } catch (error) {
      console.error('Error fetching notebooks:', error);
      toast.error('Failed to load notebooks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotebooks();
  }, [user]);

  const createNotebook = async () => {
    if (!user || !newNotebook.name.trim()) return;

    try {
      const { data, error } = await supabase
        .from('notebooks')
        .insert({
          name: newNotebook.name.trim(),
          gpu_type: newNotebook.gpu_type,
          user_id: user.id,
          status: 'starting'
        })
        .select()
        .single();

      if (error) throw error;
      
      setNotebooks(prev => [data, ...prev]);
      setCreateDialogOpen(false);
      setNewNotebook({ name: '', gpu_type: 'T4' });
      toast.success('Notebook created successfully');
      
      // Simulate starting process
      setTimeout(() => {
        setNotebooks(prev => 
          prev.map(nb => nb.id === data.id ? { ...nb, status: 'running' } : nb)
        );
      }, 3000);
    } catch (error) {
      console.error('Error creating notebook:', error);
      toast.error('Failed to create notebook');
    }
  };

  const toggleNotebook = async (notebook: Notebook) => {
    const newStatus = notebook.status === 'running' ? 'stopping' : 'starting';
    
    try {
      const { error } = await supabase
        .from('notebooks')
        .update({ status: newStatus })
        .eq('id', notebook.id);

      if (error) throw error;
      
      setNotebooks(prev => 
        prev.map(nb => nb.id === notebook.id ? { ...nb, status: newStatus } : nb)
      );

      // Simulate state change
      setTimeout(() => {
        const finalStatus = newStatus === 'starting' ? 'running' : 'stopped';
        setNotebooks(prev => 
          prev.map(nb => nb.id === notebook.id ? { ...nb, status: finalStatus } : nb)
        );
      }, 2000);
    } catch (error) {
      console.error('Error updating notebook:', error);
      toast.error('Failed to update notebook');
    }
  };

  const deleteNotebook = async (notebookId: string) => {
    try {
      const { error } = await supabase
        .from('notebooks')
        .delete()
        .eq('id', notebookId);

      if (error) throw error;
      
      setNotebooks(prev => prev.filter(nb => nb.id !== notebookId));
      toast.success('Notebook deleted');
    } catch (error) {
      console.error('Error deleting notebook:', error);
      toast.error('Failed to delete notebook');
    }
  };

  const openNotebook = (notebook: Notebook) => {
    if (notebook.status !== 'running') {
      toast.error('Notebook must be running to open');
      return;
    }
    // In production, this would open JupyterHub
    window.open(`/notebook/${notebook.id}`, '_blank');
  };

  const formatRuntime = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'default';
      case 'starting': return 'secondary';
      case 'stopping': return 'secondary';
      default: return 'outline';
    }
  };

  if (!user) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <p>Please sign in to manage your notebooks</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Notebooks</h2>
          <p className="text-muted-foreground">Jupyter notebooks with GPU acceleration</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchNotebooks}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Notebook
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Notebook</DialogTitle>
                <DialogDescription>
                  Create a new Jupyter notebook with GPU acceleration
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="notebook-name">Notebook Name</Label>
                  <Input
                    id="notebook-name"
                    placeholder="My ML Project"
                    value={newNotebook.name}
                    onChange={(e) => setNewNotebook(prev => ({ ...prev, name: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="gpu-type">GPU Type</Label>
                  <Select
                    value={newNotebook.gpu_type}
                    onValueChange={(value) => setNewNotebook(prev => ({ ...prev, gpu_type: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="T4">NVIDIA T4 (Free tier)</SelectItem>
                      <SelectItem value="V100">NVIDIA V100 ($0.50/hr)</SelectItem>
                      <SelectItem value="A100">NVIDIA A100 ($1.20/hr)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={createNotebook} className="w-full" disabled={!newNotebook.name.trim()}>
                  Create Notebook
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
      ) : notebooks.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Monitor className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No notebooks yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first notebook to start working on ML projects
            </p>
            <Button onClick={() => setCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create First Notebook
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {notebooks.map((notebook) => (
            <Card key={notebook.id}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div>
                      <h3 className="font-semibold text-lg">{notebook.name}</h3>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground mt-1">
                        <div className="flex items-center space-x-1">
                          <Cpu className="h-4 w-4" />
                          <span>{notebook.gpu_type}</span>
                        </div>
                        <Separator orientation="vertical" className="h-4" />
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span>{formatRuntime(notebook.runtime_minutes)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={getStatusColor(notebook.status)}>
                      {notebook.status}
                    </Badge>
                    {notebook.status === 'running' && (
                      <Button size="sm" variant="outline" onClick={() => openNotebook(notebook)}>
                        <ExternalLink className="h-4 w-4 mr-1" />
                        Open
                      </Button>
                    )}
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => toggleNotebook(notebook)}
                      disabled={notebook.status === 'starting' || notebook.status === 'stopping'}
                    >
                      {notebook.status === 'running' ? (
                        <Square className="h-4 w-4" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => deleteNotebook(notebook.id)}
                      disabled={notebook.status === 'running'}
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