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
import { getProducts, exportReport } from '@/lib/api';
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

  /* Main Handler */
  const handleExport = async (format: ExportFormat) => {
    // Open dialog for all real exports to select product context
    if (['pdf', 'excel', 'csv'].includes(format)) {
      setIsExporting(format);
      setIsDialogOpen(true);
      return;
    }

    // Fallback for image export (client-side usually, but here just a placeholder for now)
    setIsExporting(format);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsExporting(null);
    toast({ title: "Image export coming soon" });
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
                disabled={!isExporting} // Should be set before opening
                onClick={async () => {
                  if (!selectedProduct) return toast({ title: 'Select a product first' });

                  const format = (isExporting || 'pdf') as 'pdf' | 'excel' | 'csv';
                  toast({ title: `Generating ${format.toUpperCase()} Report...` });

                  try {
                    await exportReport(selectedProduct, format);
                    toast({ title: 'Report downloaded' });
                    setIsDialogOpen(false);
                    setExportSuccess(format);
                    setTimeout(() => setExportSuccess(null), 3000);
                  } catch (e) {
                    toast({ title: 'Failed to generate report', variant: 'destructive' });
                  } finally {
                    setIsExporting(null);
                  }
                }}
              >
                {isExporting ? `Export ${isExporting.toUpperCase()}` : 'Select & Export'}
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
