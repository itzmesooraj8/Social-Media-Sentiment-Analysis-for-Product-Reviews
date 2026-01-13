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

type ExportFormat = 'pdf' | 'excel' | 'csv' | 'png';

interface ExportButtonProps {
  className?: string;
}

export function ExportButton({ className }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState<ExportFormat | null>(null);
  const [exportSuccess, setExportSuccess] = useState<ExportFormat | null>(null);
  const { toast } = useToast();

  const handleExport = async (format: ExportFormat) => {
    setIsExporting(format);
    
    // Simulate export process
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setIsExporting(null);
    setExportSuccess(format);
    
    const formatNames = {
      pdf: 'PDF Report',
      excel: 'Excel Spreadsheet',
      csv: 'CSV Data',
      png: 'Dashboard Image',
    };
    
    toast({
      title: 'Export Complete',
      description: `${formatNames[format]} has been downloaded successfully.`,
    });
    
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
  );
}
