import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Upload, Cpu, Play, CheckCircle2, AlertTriangle } from 'lucide-react';
import { api } from '@/lib/api';

export default function ModelTraining() {
    const [datasetName, setDatasetName] = useState('');
    const [algorithm, setAlgorithm] = useState('logistic_regression');
    const [isTraining, setIsTraining] = useState(false);
    const [progress, setProgress] = useState(0);
    const [result, setResult] = useState<any>(null);

    const trainMutation = useMutation({
        mutationFn: async (data: any) => {
            // Simulate training call or call real endpoint
            // const res = await api.post('/models/train', data);
            // return res.data;

            // Simulation for demo purposes (or if endpoint not ready)
            return new Promise((resolve) => {
                let p = 0;
                const interval = setInterval(() => {
                    p += 5;
                    setProgress(p);
                    if (p >= 100) {
                        clearInterval(interval);
                        resolve({
                            accuracy: 0.89 + Math.random() * 0.05,
                            f1_score: 0.87 + Math.random() * 0.05,
                            precision: 0.88 + Math.random() * 0.05,
                            recall: 0.86 + Math.random() * 0.05,
                            model_name: `v1.2-${algorithm}`
                        });
                    }
                }, 200);
            });
        },
        onSuccess: (data: any) => {
            setIsTraining(false);
            setResult(data);
            toast.success("Training Complete", { description: `Model trained with ${data.accuracy.toFixed(2)} accuracy.` });
        },
        onError: () => {
            setIsTraining(false);
            toast.error("Training Failed");
        }
    });

    const handleTrain = () => {
        if (!datasetName) {
            toast.error("Please upload or select a dataset");
            return;
        }
        setIsTraining(true);
        setProgress(0);
        setResult(null);
        trainMutation.mutate({ dataset: datasetName, algorithm });
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Model Training Center</h2>
                    <p className="text-muted-foreground">Train and fine-tune custom sentiment models.</p>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                    {/* Configuration Panel */}
                    <Card className="glass-card border-border/50">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2"><Cpu className="h-5 w-5" /> Training Configuration</CardTitle>
                            <CardDescription>Select parameters for your new model.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label>Dataset</Label>
                                <div className="flex gap-2">
                                    <Input
                                        type="file"
                                        className="cursor-pointer file:text-foreground"
                                        onChange={(e) => setDatasetName(e.target.files?.[0]?.name || '')}
                                    />
                                </div>
                                {datasetName && <p className="text-sm text-green-500 flex items-center gap-1"><CheckCircle2 className="h-3 w-3" /> {datasetName} selected</p>}
                            </div>

                            <div className="space-y-2">
                                <Label>Algorithm</Label>
                                <Select value={algorithm} onValueChange={setAlgorithm}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="logistic_regression">Logistic Regression (Fast)</SelectItem>
                                        <SelectItem value="naive_bayes">Naive Bayes (Baseline)</SelectItem>
                                        <SelectItem value="bert_finetune">BERT Fine-tuning (Slow - GPU Required)</SelectItem>
                                        <SelectItem value="lstm">LSTM (Legacy)</SelectItem>
                                    </SelectContent>
                                </Select>
                                {algorithm === 'bert_finetune' && (
                                    <div className="p-2 bg-yellow-500/10 border border-yellow-500/20 rounded-md flex gap-2 items-start">
                                        <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5" />
                                        <p className="text-xs text-yellow-500">
                                            Warning: BERT training requires GPU access. On current environment, this may timeout or be simulated.
                                        </p>
                                    </div>
                                )}
                            </div>

                            <Button
                                onClick={handleTrain}
                                className="w-full bg-sentinel-positive text-black hover:bg-sentinel-positive/90"
                                disabled={isTraining || !datasetName}
                            >
                                {isTraining ? (
                                    <span className="flex items-center gap-2">Training... {progress}%</span>
                                ) : (
                                    <><Play className="h-4 w-4 mr-2" /> Start Training</>
                                )}
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Results Panel */}
                    <Card className="glass-card border-border/50">
                        <CardHeader>
                            <CardTitle>Training Results</CardTitle>
                            <CardDescription>Performance metrics of the trained model.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isTraining && (
                                <div className="space-y-4 py-10">
                                    <Progress value={progress} className="w-full h-2" />
                                    <p className="text-center text-sm text-muted-foreground animate-pulse">
                                        Processing dataset... tuning hyperparameters...
                                    </p>
                                </div>
                            )}

                            {!isTraining && !result && (
                                <div className="flex flex-col items-center justify-center py-10 text-muted-foreground bg-accent/20 rounded-lg border border-dashed border-border">
                                    <Cpu className="h-10 w-10 mb-2 opacity-20" />
                                    <p>No model trained yet.</p>
                                </div>
                            )}

                            {result && (
                                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-5">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-4 bg-accent/30 rounded-lg text-center">
                                            <p className="text-sm text-muted-foreground">Accuracy</p>
                                            <p className="text-3xl font-bold text-sentinel-positive">{(result.accuracy * 100).toFixed(1)}%</p>
                                        </div>
                                        <div className="p-4 bg-accent/30 rounded-lg text-center">
                                            <p className="text-sm text-muted-foreground">F1 Score</p>
                                            <p className="text-3xl font-bold text-blue-400">{(result.f1_score * 100).toFixed(1)}%</p>
                                        </div>
                                        <div className="p-4 bg-accent/30 rounded-lg text-center">
                                            <p className="text-sm text-muted-foreground">Precision</p>
                                            <p className="text-2xl font-semibold">{(result.precision * 100).toFixed(1)}%</p>
                                        </div>
                                        <div className="p-4 bg-accent/30 rounded-lg text-center">
                                            <p className="text-sm text-muted-foreground">Recall</p>
                                            <p className="text-2xl font-semibold">{(result.recall * 100).toFixed(1)}%</p>
                                        </div>
                                    </div>

                                    <div className="p-4 border border-border rounded-lg bg-background/50">
                                        <h4 className="font-semibold mb-2">Model Artifact</h4>
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="font-mono text-muted-foreground">{result.model_name}.pt</span>
                                            <Button variant="ghost" size="sm" className="h-8">Download</Button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </DashboardLayout>
    );
}
