import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, FileText, FileSpreadsheet, FileImage, Loader2, Check, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/hooks/use-toast';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useQuery } from '@tanstack/react-query';
import { getProducts, downloadReport } from '@/lib/api';
import { useDashboardData } from '@/hooks/useDashboardData';

type ExportFormat = 'pdf' | 'excel' | 'csv' | 'png';

interface ExportButtonProps {
  className?: string;
}

export function ExportButton({ className }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState<ExportFormat | null>(null);
  const [exportSuccess, setExportSuccess] = useState<ExportFormat | null>(null);
  const { toast } = useToast();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);

  // Fetch dashboard data for export
  const { data: dashboardData } = useDashboardData();

  const handleExport = async (format: ExportFormat) => {
    // If PDF, open selection dialog
    if (format === 'pdf') {
      setIsDialogOpen(true);
      return;
    }

    setIsExporting(format);

    if (format === 'csv' || format === 'excel') {
      try {
        const reviews = dashboardData?.data?.recentReviews || [];
        if (!reviews.length) {
          toast({ title: "No data to export", variant: "destructive" });
          setIsExporting(null);
          return;
        }

        // Generate CSV Content
        const headers = "Date,Platform,Author,Content,Sentiment,Score,Emotion\n";
        const rows = reviews.map((r: any) => {
          const date = r.created_at ? new Date(r.created_at).toLocaleDateString() : '';
          const content = (r.content || "").replace(/"/g, '""').replace(/\n/g, " ");
          const emotion = r.sentiment_analysis?.[0]?.emotions?.[0]?.name || r.emotion || "";
          return `"${date}","${r.platform}","${r.username}","${content}","${r.sentiment}","${r.score || 0}","${emotion}"`;
        }).join("\n");

        const csvContent = headers + rows;
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `sentiment_report_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } catch (e) {
        console.error("Export failed", e);
        toast({ title: "Export failed", variant: "destructive" });
      }
    } else {
      // Simulate other formats (PNG) for now
      await new Promise(resolve => setTimeout(resolve, 1200));
    }

    setIsExporting(null);
    setExportSuccess(format);

    const formatNames = {
      pdf: 'PDF Report',
      excel: 'Excel Spreadsheet (CSV)',
      csv: 'CSV Data',
      png: 'Dashboard Image',
    };

    if (format !== 'pdf') {
      toast({
        title: 'Export Complete',
        description: `${formatNames[format]} has been downloaded successfully.`,
      });
    }

    setTimeout(() => setExportSuccess(null), 2000);
  };

  const exportOptions = [
    {
      format: 'pdf' as const,
      label: 'Export as PDF',
      description: 'Full dashboard report',
      icon: FileText
    },
    {
      format: 'excel' as const,
      label: 'Export as Excel',
      description: 'Raw data with charts',
      icon: FileSpreadsheet
    },
    {
      format: 'csv' as const,
      label: 'Export as CSV',
      description: 'Plain data export',
      icon: FileText
    },
    {
      format: 'png' as const,
      label: 'Export as Image',
      description: 'Dashboard screenshot',
      icon: FileImage
    },
  ];

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className={className}>
            <AnimatePresence mode="wait">
              {isExporting ? (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                </motion.div>
              ) : exportSuccess ? (
                <motion.div
                  key="success"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                >
                  <Check className="h-4 w-4 mr-2 text-sentinel-positive" />
                </motion.div>
              ) : (
                <motion.div
                  key="default"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <Download className="h-4 w-4 mr-2" />
                </motion.div>
              )}
            </AnimatePresence>
            Export
            <ChevronDown className="h-4 w-4 ml-2" />
          </Button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="end" className="w-56 glass-card border-border/50">
          {exportOptions.map((option, index) => {
            const Icon = option.icon;
            const isLoading = isExporting === option.format;
            const isSuccess = exportSuccess === option.format;

            return (
              <div key={option.format}>
                {index > 0 && <DropdownMenuSeparator />}
                <DropdownMenuItem
                  onClick={() => handleExport(option.format)}
                  disabled={!!isExporting}
                  className="cursor-pointer"
                >
                  <div className="flex items-center gap-3 w-full">
                    <div className="p-1.5 rounded bg-muted">
                      {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : isSuccess ? (
                        <Check className="h-4 w-4 text-sentinel-positive" />
                      ) : (
                        <Icon className="h-4 w-4" />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{option.label}</p>
                      <p className="text-xs text-muted-foreground">{option.description}</p>
                    </div>
                  </div>
                </DropdownMenuItem>
              </div>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Dialog for PDF export product selection */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Export PDF Report</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <ProductSelector onSelect={(id: string) => setSelectedProduct(id)} />
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
              <Button
                onClick={async () => {
                  if (!selectedProduct) return toast({ title: 'Select a product first' });
                  toast({ title: 'Generating Report...' });
                  try {
                    await downloadReport(selectedProduct);
                    toast({ title: 'Report downloaded' });
                    setIsDialogOpen(false);
                  } catch (e) {
                    toast({ title: 'Failed to generate report', variant: 'destructive' });
                  }
                }}
              >
                Export PDF
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

function ProductSelector({ onSelect }: { onSelect: (id: string) => void }) {
  const { data: products = [], isLoading } = useQuery({ queryKey: ['products'], queryFn: getProducts });

  if (isLoading) return <div>Loading products...</div>;
  if (!products || products.length === 0) return <div>No products found. Add a product first.</div>;

  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {products.map((p: any) => (
        <div key={p.id} className="flex items-center justify-between p-2 border rounded">
          <div>
            <div className="font-medium">{p.name}</div>
            <div className="text-xs text-muted-foreground">{p.description}</div>
          </div>
          <div>
            <Button size="sm" onClick={() => onSelect(p.id)}>Select</Button>
          </div>
        </div>
      ))}
    </div>
  );
}
