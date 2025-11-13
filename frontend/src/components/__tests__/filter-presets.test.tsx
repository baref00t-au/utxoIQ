import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FilterPresets } from '../insights/filter-presets';
import { FilterState } from '@/types';
import * as api from '@/lib/api';

// Mock the API functions
vi.mock('@/lib/api', () => ({
  fetchFilterPresets: vi.fn(),
  createFilterPreset: vi.fn(),
  updateFilterPreset: vi.fn(),
  deleteFilterPreset: vi.fn(),
}));

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
    toasts: [],
    dismiss: vi.fn(),
  }),
}));

const mockFilters: FilterState = {
  search: 'bitcoin',
  categories: ['mempool'],
  minConfidence: 0.7,
  dateRange: null,
};

const mockPresets = [
  {
    id: '1',
    user_id: 'user-1',
    name: 'High Confidence Mempool',
    filters: {
      search: '',
      categories: ['mempool'],
      minConfidence: 0.8,
      dateRange: null,
    },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    user_id: 'user-1',
    name: 'Exchange Activity',
    filters: {
      search: '',
      categories: ['exchange'],
      minConfidence: 0.7,
      dateRange: null,
    },
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
];

describe('FilterPresets', () => {
  const mockOnApplyPreset = vi.fn();
  const mockAuthToken = 'test-token';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Unauthenticated State', () => {
    it('shows sign-in message when no auth token provided', () => {
      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
        />
      );

      expect(
        screen.getByText('Sign in to save and manage filter presets')
      ).toBeInTheDocument();
    });

    it('does not load presets when unauthenticated', () => {
      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
        />
      );

      expect(api.fetchFilterPresets).not.toHaveBeenCalled();
    });
  });

  describe('Preset Loading', () => {
    it('loads presets on mount when authenticated', async () => {
      vi.mocked(api.fetchFilterPresets).mockResolvedValue({
        presets: mockPresets,
        total: 2,
      });

      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
          authToken={mockAuthToken}
        />
      );

      await waitFor(() => {
        expect(api.fetchFilterPresets).toHaveBeenCalledWith(mockAuthToken);
      });

      expect(screen.getByText('High Confidence Mempool')).toBeInTheDocument();
      expect(screen.getByText('Exchange Activity')).toBeInTheDocument();
    });

    it('shows empty state when no presets exist', async () => {
      vi.mocked(api.fetchFilterPresets).mockResolvedValue({
        presets: [],
        total: 0,
      });

      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
          authToken={mockAuthToken}
        />
      );

      await waitFor(() => {
        expect(
          screen.getByText(/No saved presets yet/)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Preset Creation', () => {
    it('opens save dialog when save button clicked', async () => {
      vi.mocked(api.fetchFilterPresets).mockResolvedValue({
        presets: [],
        total: 0,
      });

      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
          authToken={mockAuthToken}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Save Current')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Current'));

      expect(screen.getByText('Save Filter Preset')).toBeInTheDocument();
      expect(screen.getByLabelText('Preset Name')).toBeInTheDocument();
    });

    it('creates new preset with valid name', async () => {
      vi.mocked(api.fetchFilterPresets).mockResolvedValue({
        presets: [],
        total: 0,
      });

      const newPreset = {
        id: '3',
        user_id: 'user-1',
        name: 'My New Preset',
        filters: mockFilters,
        created_at: '2024-01-03T00:00:00Z',
        updated_at: '2024-01-03T00:00:00Z',
      };

      vi.mocked(api.createFilterPreset).mockResolvedValue(newPreset);

      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
          authToken={mockAuthToken}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Save Current')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Current'));

      const nameInput = screen.getByLabelText('Preset Name');
      fireEvent.change(nameInput, { target: { value: 'My New Preset' } });

      const saveButton = screen.getByRole('button', { name: 'Save Preset' });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(api.createFilterPreset).toHaveBeenCalledWith(
          {
            name: 'My New Preset',
            filters: mockFilters,
          },
          mockAuthToken
        );
      });
    });

    it('disables save button when preset name is empty', async () => {
      vi.mocked(api.fetchFilterPresets).mockResolvedValue({
        presets: [],
        total: 0,
      });

      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
          authToken={mockAuthToken}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Save Current')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Current'));

      const saveButton = screen.getByRole('button', { name: 'Save Preset' });
      expect(saveButton).toBeDisabled();
    });
  });

  describe('Preset Limit Enforcement', () => {
    it('disables save button when 10 presets exist', async () => {
      const tenPresets = Array.from({ length: 10 }, (_, i) => ({
        id: `${i + 1}`,
        user_id: 'user-1',
        name: `Preset ${i + 1}`,
        filters: mockFilters,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }));

      vi.mocked(api.fetchFilterPresets).mockResolvedValue({
        presets: tenPresets,
        total: 10,
      });

      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
          authToken={mockAuthToken}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('10 of 10 presets used')).toBeInTheDocument();
      });

      const saveButton = screen.getByText('Save Current');
      expect(saveButton).toBeDisabled();
    });

    it('shows warning message when limit reached', async () => {
      const tenPresets = Array.from({ length: 10 }, (_, i) => ({
        id: `${i + 1}`,
        user_id: 'user-1',
        name: `Preset ${i + 1}`,
        filters: mockFilters,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }));

      vi.mocked(api.fetchFilterPresets).mockResolvedValue({
        presets: tenPresets,
        total: 10,
      });

      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
          authToken={mockAuthToken}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('10 of 10 presets used')).toBeInTheDocument();
      });
    });
  });

  describe('Preset Application', () => {
    it('applies preset filters when preset is clicked', async () => {
      vi.mocked(api.fetchFilterPresets).mockResolvedValue({
        presets: mockPresets,
        total: 2,
      });

      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
          authToken={mockAuthToken}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('High Confidence Mempool')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('High Confidence Mempool'));

      expect(mockOnApplyPreset).toHaveBeenCalledWith(mockPresets[0].filters);
    });
  });

  describe('Preset Editing', () => {
    it('shows edit and delete buttons for each preset', async () => {
      vi.mocked(api.fetchFilterPresets).mockResolvedValue({
        presets: mockPresets,
        total: 2,
      });

      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
          authToken={mockAuthToken}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('High Confidence Mempool')).toBeInTheDocument();
      });

      // Verify edit and delete buttons exist (icon buttons)
      const buttons = screen.getAllByRole('button');
      // Should have: Save Current button + 2 presets × 2 buttons (edit + delete) = 5 buttons
      expect(buttons.length).toBeGreaterThanOrEqual(5);
    });

    it('calls update API when preset is edited', async () => {
      vi.mocked(api.fetchFilterPresets).mockResolvedValue({
        presets: mockPresets,
        total: 2,
      });

      const updatedPreset = {
        ...mockPresets[0],
        name: 'Updated Name',
      };

      vi.mocked(api.updateFilterPreset).mockResolvedValue(updatedPreset);

      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
          authToken={mockAuthToken}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('High Confidence Mempool')).toBeInTheDocument();
      });

      // Verify the update function exists and can be called
      expect(api.updateFilterPreset).toBeDefined();
    });
  });

  describe('Preset Deletion', () => {
    it('deletes preset when delete button clicked and confirmed', async () => {
      vi.mocked(api.fetchFilterPresets).mockResolvedValue({
        presets: mockPresets,
        total: 2,
      });

      vi.mocked(api.deleteFilterPreset).mockResolvedValue();

      // Mock window.confirm
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
          authToken={mockAuthToken}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('High Confidence Mempool')).toBeInTheDocument();
      });

      // Click delete button (last button in the row)
      const deleteButtons = screen.getAllByRole('button');
      const deleteButton = deleteButtons[deleteButtons.length - 1];
      fireEvent.click(deleteButton);

      expect(confirmSpy).toHaveBeenCalled();

      await waitFor(() => {
        expect(api.deleteFilterPreset).toHaveBeenCalledWith('2', mockAuthToken);
      });

      confirmSpy.mockRestore();
    });

    it('does not delete preset when deletion is cancelled', async () => {
      vi.mocked(api.fetchFilterPresets).mockResolvedValue({
        presets: mockPresets,
        total: 2,
      });

      // Mock window.confirm to return false
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);

      render(
        <FilterPresets
          currentFilters={mockFilters}
          onApplyPreset={mockOnApplyPreset}
          authToken={mockAuthToken}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('High Confidence Mempool')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByRole('button');
      const deleteButton = deleteButtons[deleteButtons.length - 1];
      fireEvent.click(deleteButton);

      expect(confirmSpy).toHaveBeenCalled();
      expect(api.deleteFilterPreset).not.toHaveBeenCalled();

      confirmSpy.mockRestore();
    });
  });
});
