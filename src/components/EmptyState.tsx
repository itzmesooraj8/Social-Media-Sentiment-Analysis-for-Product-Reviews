import { motion } from 'framer-motion';
import { Package, Plus, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

interface EmptyStateProps {
    icon?: React.ComponentType<{ className?: string }>;
    title: string;
    description: string;
    actionLabel?: string;
    onAction?: () => void;
}

export function EmptyState({
    icon: Icon = Package,
    title,
    description,
    actionLabel,
    onAction
}: EmptyStateProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center min-h-[400px] glass-card p-12 text-center"
        >
            <div className="p-4 rounded-full bg-sentinel-credibility/10 mb-4">
                <Icon className="h-12 w-12 text-sentinel-credibility" />
            </div>
            <h3 className="text-2xl font-bold mb-2">{title}</h3>
            <p className="text-muted-foreground mb-6 max-w-md">{description}</p>
            {actionLabel && onAction && (
                <Button
                    onClick={onAction}
                    className="bg-sentinel-credibility hover:bg-sentinel-credibility/90"
                >
                    <Plus className="h-4 w-4 mr-2" />
                    {actionLabel}
                </Button>
            )}
        </motion.div>
    );
}

export function EmptyDashboard() {
    const navigate = useNavigate();

    return (
        <div className="space-y-6">
            <EmptyState
                icon={Package}
                title="Welcome to Sentiment Beacon"
                description="Get started by adding your first product to track sentiment analysis across social media platforms."
                actionLabel="Add Your First Product"
                onAction={() => navigate('/products')}
            />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="glass-card p-6 text-center">
                    <div className="text-3xl font-bold text-sentinel-positive mb-2">1</div>
                    <p className="text-sm text-muted-foreground">Add Products</p>
                </div>
                <div className="glass-card p-6 text-center">
                    <div className="text-3xl font-bold text-sentinel-credibility mb-2">2</div>
                    <p className="text-sm text-muted-foreground">Collect Reviews</p>
                </div>
                <div className="glass-card p-6 text-center">
                    <div className="text-3xl font-bold text-sentinel-positive mb-2">3</div>
                    <p className="text-sm text-muted-foreground">Analyze Sentiment</p>
                </div>
            </div>
        </div>
    );
}
