import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { 
  Play, 
  Square, 
  Cpu, 
  HardDrive, 
  Zap, 
  DollarSign, 
  FileCode, 
  Rocket,
  Monitor,
  Clock,
  BarChart3
} from "lucide-react";

const Index = () => {
  const [activeTab, setActiveTab] = useState("dashboard");

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
            <Badge variant="secondary" className="text-sm">
              <Zap className="h-4 w-4 mr-1" />
              $12.50 credits
            </Badge>
            <Button size="sm">Account</Button>
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Notebooks</CardTitle>
                  <FileCode className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">2</div>
                  <p className="text-xs text-muted-foreground">Running on GPU</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Deployed Models</CardTitle>
                  <Rocket className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">5</div>
                  <p className="text-xs text-muted-foreground">Live endpoints</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">GPU Hours</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">24.5</div>
                  <p className="text-xs text-muted-foreground">This month</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">API Calls</CardTitle>
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">1,240</div>
                  <p className="text-xs text-muted-foreground">Last 7 days</p>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Quick Start</CardTitle>
                  <CardDescription>Launch a new notebook or deploy a model</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button className="w-full justify-start">
                    <Play className="h-4 w-4 mr-2" />
                    New Notebook
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
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
                      <span>GPU Usage</span>
                      <span>2/8 GPUs</span>
                    </div>
                    <Progress value={25} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Storage</span>
                      <span>45GB/100GB</span>
                    </div>
                    <Progress value={45} className="h-2" />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="notebooks">
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Notebooks</h2>
                <Button>
                  <Play className="h-4 w-4 mr-2" />
                  New Notebook
                </Button>
              </div>

              <div className="grid gap-4">
                {[
                  { name: "Image Classification", status: "running", gpu: "A100", runtime: "2h 15m" },
                  { name: "NLP Fine-tuning", status: "stopped", gpu: "V100", runtime: "0h 0m" },
                  { name: "Data Analysis", status: "running", gpu: "T4", runtime: "45m" }
                ].map((notebook, i) => (
                  <Card key={i}>
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div>
                            <h3 className="font-semibold">{notebook.name}</h3>
                            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                              <Cpu className="h-4 w-4" />
                              <span>{notebook.gpu}</span>
                              <Separator orientation="vertical" className="h-4" />
                              <Clock className="h-4 w-4" />
                              <span>{notebook.runtime}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge variant={notebook.status === "running" ? "default" : "secondary"}>
                            {notebook.status}
                          </Badge>
                          <Button size="sm" variant="outline">
                            {notebook.status === "running" ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="models">
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Deployed Models</h2>
                <Button>
                  <Rocket className="h-4 w-4 mr-2" />
                  Deploy New Model
                </Button>
              </div>

              <div className="grid gap-4">
                {[
                  { name: "resnet50-classifier", endpoint: "api/v1/classify", calls: 450, latency: "120ms" },
                  { name: "bert-sentiment", endpoint: "api/v1/sentiment", calls: 230, latency: "85ms" },
                  { name: "gpt2-generator", endpoint: "api/v1/generate", calls: 120, latency: "340ms" }
                ].map((model, i) => (
                  <Card key={i}>
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold">{model.name}</h3>
                          <p className="text-sm text-muted-foreground font-mono">{model.endpoint}</p>
                          <div className="flex items-center space-x-4 mt-2 text-sm text-muted-foreground">
                            <span>{model.calls} calls today</span>
                            <Separator orientation="vertical" className="h-4" />
                            <span>Avg: {model.latency}</span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge variant="default">Live</Badge>
                          <Button size="sm" variant="outline">Configure</Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
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
                    <div className="text-3xl font-bold text-primary">$12.50</div>
                    <p className="text-sm text-muted-foreground">Available credits</p>
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
                    <div className="text-2xl font-bold">$8.40</div>
                    <p className="text-sm text-muted-foreground">This month</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <HardDrive className="h-5 w-5 mr-2" />
                      API Calls
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">$2.10</div>
                    <p className="text-sm text-muted-foreground">This month</p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Usage Breakdown</CardTitle>
                  <CardDescription>Pay-as-you-go pricing details</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span>A100 GPU ($2.50/hour)</span>
                      <span>2.5 hours - $6.25</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>V100 GPU ($1.20/hour)</span>
                      <span>1.8 hours - $2.15</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>API Calls ($0.002/call)</span>
                      <span>1,240 calls - $2.48</span>
                    </div>
                    <Separator />
                    <div className="flex justify-between items-center font-semibold">
                      <span>Total Usage</span>
                      <span>$10.88</span>
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
