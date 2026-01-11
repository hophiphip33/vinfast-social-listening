// Component Badge hiển thị trạng thái với màu sắc phù hợp
import { cn } from '@/lib/utils';

type StatusType = 
  | 'Active' | 'Banned' | 'Inactive'
  | 'Positive' | 'Negative' | 'Neutral' 
  | 'Free' | 'Premium' | 'Enterprise';

interface StatusBadgeProps {
  status: StatusType;
}

const StatusBadge = ({ status }: StatusBadgeProps) => {
  const statusStyles: Record<StatusType, string> = {
    Active: 'bg-success/20 text-success border-success/30',
    Banned: 'bg-destructive/20 text-destructive border-destructive/30',
    Inactive: 'bg-muted text-muted-foreground border-border',
    Positive: 'bg-success/20 text-success border-success/30',
    Negative: 'bg-destructive/20 text-destructive border-destructive/30',
    Neutral: 'bg-muted text-muted-foreground border-border',
    Free: 'bg-secondary text-secondary-foreground border-border',
    Premium: 'bg-primary/20 text-primary border-primary/30',
    Enterprise: 'bg-warning/20 text-warning border-warning/30',
  };

  return (
    <span className={cn(
      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
      statusStyles[status]
    )}>
      {status}
    </span>
  );
};

export default StatusBadge;
