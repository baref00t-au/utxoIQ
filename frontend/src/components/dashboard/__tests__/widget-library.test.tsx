import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WidgetLibrary } from '../widget-library';

describe('WidgetLibrary', () => {
  it('renders add widget button', () => {
    const onAddWidget = vi.fn();
    render(<WidgetLibrary onAddWidget={onAddWidget} />);

    expect(screen.getByText('Add Widget')).toBeInTheDocument();
  });

  it('opens dialog when button is clicked', async () => {
    const onAddWidget = vi.fn();
    render(<WidgetLibrary onAddWidget={onAddWidget} />);

    fireEvent.click(screen.getByText('Add Widget'));

    await waitFor(() => {
      expect(screen.getByText('Widget Library')).toBeInTheDocument();
    });
  });

  it('displays all widget templates', async () => {
    const onAddWidget = vi.fn();
    render(<WidgetLibrary onAddWidget={onAddWidget} />);

    fireEvent.click(screen.getByText('Add Widget'));

    await waitFor(() => {
      expect(screen.getByText('Line Chart')).toBeInTheDocument();
      expect(screen.getByText('Bar Chart')).toBeInTheDocument();
      expect(screen.getByText('Gauge')).toBeInTheDocument();
      expect(screen.getByText('Stat Card')).toBeInTheDocument();
    });
  });

  it('calls onAddWidget when template is selected', async () => {
    const onAddWidget = vi.fn();
    render(<WidgetLibrary onAddWidget={onAddWidget} />);

    fireEvent.click(screen.getByText('Add Widget'));

    await waitFor(() => {
      expect(screen.getByText('Line Chart')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Line Chart'));

    await waitFor(() => {
      expect(onAddWidget).toHaveBeenCalledTimes(1);
      expect(onAddWidget).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'line_chart',
          title: 'Line Chart',
        })
      );
    });
  });

  it('closes dialog after adding widget', async () => {
    const onAddWidget = vi.fn();
    render(<WidgetLibrary onAddWidget={onAddWidget} />);

    fireEvent.click(screen.getByText('Add Widget'));

    await waitFor(() => {
      expect(screen.getByText('Line Chart')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Line Chart'));

    await waitFor(() => {
      expect(screen.queryByText('Widget Library')).not.toBeInTheDocument();
    });
  });
});
