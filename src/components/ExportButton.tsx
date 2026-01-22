
import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface ExportButtonProps {
  productId: string;
}

export const ExportButton: React.FC<ExportButtonProps> = ({ productId }) => {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleExport = async (format: 'csv' | 'pdf') => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/reports/export?product_id=${productId}&format=${format}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`, // Ensure you handle auth token
        },
      });

      if (!response.ok) throw new Error('Export failed');

      // Create a blob from the response
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${productId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Export Successful",
        description: `Your ${format.toUpperCase()} report has been downloaded.`,
      });
    } catch (error) {
      toast({
        title: "Export Failed",
        description: "Could not generate report. Please try again.",
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
