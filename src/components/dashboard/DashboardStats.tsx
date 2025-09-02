import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileCode, Rocket, Clock, BarChart3 } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/components/auth/AuthProvider';

interface DashboardStats {
  activeNotebooks: number;
  deployedModels: number;
  gpuHours: number;
  apiCalls: number;
}

export const DashboardStats = () => {
  const [stats, setStats] = useState<DashboardStats>({
    activeNotebooks: 0,
    deployedModels: 0,
    gpuHours: 0,
    apiCalls: 0
  });
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  const fetchStats = async () => {
    if (!user) return;

    try {
      // Fetch notebooks count
      const { count: notebooksCount } = await supabase
        .from('notebooks')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', user.id)
        .eq('status', 'running');

      // Fetch models count
      const { count: modelsCount } = await supabase
        .from('deployed_models')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', user.id)
        .eq('status', 'deployed');

      // Fetch usage stats
      const { data: usageData } = await supabase
        .from('usage_logs')
        .select('resource_type, usage_amount')
        .eq('user_id', user.id)
        .gte('created_at', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString());

      let gpuHours = 0;
      let apiCalls = 0;

      usageData?.forEach(log => {
        if (log.resource_type === 'notebook') {
          gpuHours += Number(log.usage_amount);
        } else if (log.resource_type === 'api_call') {
          apiCalls += Number(log.usage_amount);
        }
      });

      setStats({
        activeNotebooks: notebooksCount || 0,
        deployedModels: modelsCount || 0,
        gpuHours: Math.round(gpuHours * 10) / 10,
        apiCalls
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [user]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map(i => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-muted rounded w-1/2"></div>
                <div className="h-8 bg-muted rounded w-1/3"></div>
                <div className="h-3 bg-muted rounded w-2/3"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Notebooks</CardTitle>
          <FileCode className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.activeNotebooks}</div>
          <p className="text-xs text-muted-foreground">Running on GPU</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Deployed Models</CardTitle>
          <Rocket className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.deployedModels}</div>
          <p className="text-xs text-muted-foreground">Live endpoints</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">GPU Hours</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.gpuHours}</div>
          <p className="text-xs text-muted-foreground">This month</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">API Calls</CardTitle>
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.apiCalls.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">Last 30 days</p>
        </CardContent>
      </Card>
    </div>
  );
};