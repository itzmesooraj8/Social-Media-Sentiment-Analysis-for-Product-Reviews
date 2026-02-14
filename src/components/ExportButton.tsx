import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { exportReport } from '@/lib/api';

interface ExportButtonProps {
  productId: string;
}

export const ExportButton: React.FC<ExportButtonProps> = ({ productId }) => {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleExport = async (format: 'csv' | 'pdf') => {
    try {
      setLoading(true);
      toast({
        title: "Generating Report",
        description: `Your ${format.toUpperCase()} report is being prepared...`,
      });

      await exportReport(productId, format);

      toast({
        title: "Export Successful",
        description: `Your ${format.toUpperCase()} report has been downloaded.`,
      });
    } catch (error) {
      toast({
        title: "Export Failed",
        description: "Could not generate report. Please ensure your backend is live and the 'reports' bucket exists in Supabase.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('csv')}
        disabled={loading}
      >
        <Download className="mr-2 h-4 w-4" />
        Export CSV
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('pdf')}
        disabled={loading}
      >
        <Download className="mr-2 h-4 w-4" />
        Export PDF
      </Button>
    </div>
  );
};
