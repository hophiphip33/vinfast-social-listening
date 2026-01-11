// Component hiển thị một chỉ số Metric với biểu đồ mini
import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  color?: 'primary' | 'success' | 'warning' | 'destructive';
}

const MetricCard = ({ 
  title, 
  value, 
  icon, 
  trend, 
  trendValue,
  color = 'primary' 
}: MetricCardProps) => {
  const colorClasses = {
    primary: 'text-primary border-primary/30',
    success: 'text-success border-success/30',
    warning: 'text-warning border-warning/30',
    destructive: 'text-destructive border-destructive/30',
  };

  const bgClasses = {
    primary: 'bg-primary/10',
    success: 'bg-success/10',
    warning: 'bg-warning/10',
    destructive: 'bg-destructive/10',
  };

  return (
    <div className="gradient-card rounded-lg border border-border p-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className={cn("text-3xl font-semibold", colorClasses[color])}>
            {value}
          </p>
          {trend && trendValue && (
            <div className="flex items-center gap-1 text-xs">
              <span className={cn(
                trend === 'up' && 'text-success',
                trend === 'down' && 'text-destructive',
                trend === 'stable' && 'text-muted-foreground'
              )}>
                {trend === 'up' && '↑'}
                {trend === 'down' && '↓'}
                {trend === 'stable' && '→'}
                {trendValue}
              </span>
            </div>
          )}
        </div>
        <div className={cn(
          "p-3 rounded-lg",
          bgClasses[color],
          colorClasses[color]
        )}>
          {icon}
        </div>
      </div>
    </div>
  );
};

export default MetricCard;
