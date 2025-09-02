import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { 
  Play, 
  Cpu, 
  HardDrive, 
  Zap, 
  DollarSign, 
  Rocket,
  Monitor,
  User,
  LogOut
} from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import { NotebookManager } from "@/components/notebooks/NotebookManager";
import { ModelManager } from "@/components/models/ModelManager";
import { DashboardStats } from "@/components/dashboard/DashboardStats";

const Index = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const { user, signOut, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !user) {
      navigate('/auth');
    }
  }, [user, loading, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Monitor className="h-12 w-12 mx-auto text-primary mb-4 animate-pulse" />
          <p className="text-lg font-medium">Loading MLCloud...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect to auth
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Monitor className="h-8 w-8 text-primary" />
            <h1 className="text-2xl font-bold text-foreground">MLCloud</h1>
          </div>
          <div className="flex items-center space-x-4">
            {user && (
              <>
                <Badge variant="secondary" className="text-sm">
                  <Zap className="h-4 w-4 mr-1" />
                  $10.00 free credits
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {user.email}
                </span>
                <Button size="sm" variant="outline" onClick={signOut}>
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </Button>
              </>
            )}
            {!user && (
              <Button size="sm" onClick={() => navigate('/auth')}>
                <User className="h-4 w-4 mr-2" />
                Sign In
              </Button>
            )}
          </div>
        </div>
      </header>

        <div className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-6">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="notebooks">Notebooks</TabsTrigger>
            <TabsTrigger value="models">Models</TabsTrigger>
            <TabsTrigger value="billing">Billing</TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard">
            <DashboardStats />
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
              <Card>
                <CardHeader>
                  <CardTitle>Quick Start</CardTitle>
                  <CardDescription>Launch a new notebook or deploy a model</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button className="w-full justify-start" onClick={() => setActiveTab("notebooks")}>
                    <Play className="h-4 w-4 mr-2" />
                    New Notebook
                  </Button>
                  <Button variant="outline" className="w-full justify-start" onClick={() => setActiveTab("models")}>
                    <Rocket className="h-4 w-4 mr-2" />
                    Deploy Model
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Resource Usage</CardTitle>
                  <CardDescription>Current GPU and storage consumption</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Free Credits</span>
                      <span>$10.00/$10.00</span>
                    </div>
                    <Progress value={100} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Storage</span>
                      <span>2GB/100GB</span>
                    </div>
                    <Progress value={2} className="h-2" />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="notebooks">
            <NotebookManager />
          </TabsContent>

          <TabsContent value="models">
            <ModelManager />
          </TabsContent>

          <TabsContent value="billing">
            <div className="space-y-6">
              <h2 className="text-2xl font-bold">Billing & Usage</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <DollarSign className="h-5 w-5 mr-2" />
                      Current Balance
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-primary">$10.00</div>
                    <p className="text-sm text-muted-foreground">Free credits remaining</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Cpu className="h-5 w-5 mr-2" />
                      GPU Usage
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">$0.00</div>
                    <p className="text-sm text-muted-foreground">This month</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <HardDrive className="h-5 w-5 mr-2" />
                      Storage & API
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">$0.00</div>
                    <p className="text-sm text-muted-foreground">This month</p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Free Tier Benefits</CardTitle>
                  <CardDescription>What's included in your free MLCloud account</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <h4 className="font-medium">Included Free:</h4>
                      <ul className="space-y-2 text-sm text-muted-foreground">
                        <li>• $10.00 GPU credits (NVIDIA T4)</li>
                        <li>• 100GB storage space</li>
                        <li>• Unlimited public notebooks</li>
                        <li>• 10,000 API calls/month</li>
                        <li>• Community support</li>
                      </ul>
                    </div>
                    <div className="space-y-4">
                      <h4 className="font-medium">Usage-based Pricing:</h4>
                      <ul className="space-y-2 text-sm text-muted-foreground">
                        <li>• T4 GPU: Free (first $10)</li>
                        <li>• V100 GPU: $0.50/hour</li>
                        <li>• A100 GPU: $1.20/hour</li>
                        <li>• Storage: $0.10/GB/month</li>
                        <li>• API calls: $0.002/call (after free tier)</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
