import { type LucideIcon } from "lucide-react";
import Link from "next/link";

interface EmptyStateProps {
  icon: LucideIcon;
  iconColor?: string;
  iconBg?: string;
  title: string;
  description: string;
  action?: { label: string; href?: string; onClick?: () => void };
  secondaryAction?: { label: string; href?: string; onClick?: () => void };
  className?: string;
}

export function EmptyState({
  icon: Icon,
  iconColor = "text-gray-300",
  iconBg = "bg-gray-50",
  title,
  description,
  action,
  secondaryAction,
  className = "",
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 px-6 text-center ${className}`}>
      <div className={`w-12 h-12 rounded-2xl ${iconBg} border border-gray-100 flex items-center justify-center mb-3`}>
        <Icon className={`w-6 h-6 ${iconColor}`} />
      </div>
      <p className="text-sm font-semibold text-gray-700 mb-1">{title}</p>
      <p className="text-xs text-gray-400 max-w-[22rem] leading-relaxed">{description}</p>
      {(action || secondaryAction) && (
        <div className="flex items-center gap-3 mt-4">
          {action && (
            action.href ? (
              <Link href={action.href} className="btn-primary text-xs px-4 py-2">
                {action.label}
              </Link>
            ) : (
              <button onClick={action.onClick} className="btn-primary text-xs px-4 py-2">
                {action.label}
              </button>
            )
          )}
          {secondaryAction && (
            secondaryAction.href ? (
              <Link href={secondaryAction.href} className="text-xs text-brand-600 hover:text-brand-700 font-medium">
                {secondaryAction.label}
              </Link>
            ) : (
              <button onClick={secondaryAction.onClick} className="text-xs text-brand-600 hover:text-brand-700 font-medium">
                {secondaryAction.label}
              </button>
            )
          )}
        </div>
      )}
    </div>
  );
}
