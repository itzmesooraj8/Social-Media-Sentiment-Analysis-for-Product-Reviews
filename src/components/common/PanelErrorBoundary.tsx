import React, { Component } from 'react';

interface PanelErrorBoundaryProps {
  children: React.ReactNode;
  title?: string;
}

interface PanelErrorBoundaryState {
  hasError: boolean;
}

export class PanelErrorBoundary extends Component<PanelErrorBoundaryProps, PanelErrorBoundaryState> {
  constructor(props: PanelErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): PanelErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Panel render error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-xl border border-border/60 bg-card/70 p-5">
          <p className="text-sm font-semibold text-foreground">
            {this.props.title || 'Panel'} unavailable
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            This section failed to render. Refresh the page or retry data sync.
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}
