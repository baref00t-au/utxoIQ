'use client';

import { SignalType, FilterState } from '@/types';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { Search, Calendar as CalendarIcon, X } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { FilterPresets } from './filter-presets';
import { useAuth } from '@/lib/auth-context';

interface InsightFiltersProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  resultCount: number;
}

const CATEGORIES: { value: SignalType; label: string }[] = [
  { value: 'mempool', label: 'Mempool' },
  { value: 'exchange', label: 'Exchange' },
  { value: 'miner', label: 'Miner' },
  { value: 'whale', label: 'Whale' },
];

export function InsightFilters({
  filters,
  onFiltersChange,
  resultCount,
}: InsightFiltersProps) {
  const { user, firebaseUser } = useAuth();
  const [authToken, setAuthToken] = useState<string | undefined>();

  // Get auth token for filter presets
  useEffect(() => {
    const loadToken = async () => {
      if (firebaseUser) {
        const token = await firebaseUser.getIdToken();
        setAuthToken(token);
      }
    };
    loadToken();
  }, [firebaseUser]);

  const handleSearchChange = (search: string) => {
    onFiltersChange({ ...filters, search });
  };

  const handleCategoryToggle = (category: SignalType) => {
    const newCategories = filters.categories.includes(category)
      ? filters.categories.filter((c) => c !== category)
      : [...filters.categories, category];
    onFiltersChange({ ...filters, categories: newCategories });
  };

  const handleConfidenceChange = (value: number[]) => {
    onFiltersChange({ ...filters, minConfidence: value[0] });
  };

  const handleDateRangeChange = (range: { start: Date; end: Date } | null) => {
    onFiltersChange({ ...filters, dateRange: range });
  };

  const handleClearFilters = () => {
    onFiltersChange({
      search: '',
      categories: [],
      minConfidence: 0,
      dateRange: null,
    });
  };

  const hasActiveFilters =
    filters.search ||
    filters.categories.length > 0 ||
    filters.minConfidence > 0 ||
    filters.dateRange !== null;

  return (
    <div className="space-y-6">
      {/* Filter Presets */}
      <FilterPresets
        currentFilters={filters}
        onApplyPreset={onFiltersChange}
        authToken={authToken}
      />

      {/* Filters Panel */}
      <div className="rounded-2xl border border-border bg-card p-6 space-y-6">
        {/* Search Input */}
      <div>
        <Label htmlFor="search" className="text-sm font-medium mb-2 block">
          Search
        </Label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            id="search"
            type="text"
            placeholder="Search insights... (Press / to focus)"
            value={filters.search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-9"
            aria-label="Search insights"
            data-search-input
          />
        </div>
      </div>

      {/* Category Multi-Select */}
      <div>
        <Label className="text-sm font-medium mb-3 block">Categories</Label>
        <div className="space-y-2">
          {CATEGORIES.map((category) => (
            <div key={category.value} className="flex items-center space-x-2">
              <Checkbox
                id={`category-${category.value}`}
                checked={filters.categories.includes(category.value)}
                onCheckedChange={() => handleCategoryToggle(category.value)}
              />
              <Label
                htmlFor={`category-${category.value}`}
                className="text-sm font-normal cursor-pointer"
              >
                {category.label}
              </Label>
            </div>
          ))}
        </div>
      </div>

      {/* Confidence Score Slider */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <Label htmlFor="confidence-slider" className="text-sm font-medium">
            Minimum Confidence
          </Label>
          <span className="text-sm text-muted-foreground">
            {Math.round(filters.minConfidence * 100)}%
          </span>
        </div>
        <Slider
          id="confidence-slider"
          min={0}
          max={1}
          step={0.05}
          value={[filters.minConfidence]}
          onValueChange={handleConfidenceChange}
          className="w-full"
          aria-label="Minimum confidence score"
        />
        <div className="flex justify-between text-xs text-muted-foreground mt-1">
          <span>0%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Date Range Picker */}
      <div>
        <Label className="text-sm font-medium mb-3 block">Date Range</Label>
        <DateRangePicker
          dateRange={filters.dateRange}
          onDateRangeChange={handleDateRangeChange}
        />
      </div>

      {/* Result Count */}
      <div className="pt-4 border-t border-border">
        <div className="text-sm text-muted-foreground">
          <span className="font-medium text-foreground">{resultCount}</span>{' '}
          {resultCount === 1 ? 'result' : 'results'}
        </div>
      </div>

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearFilters}
            className="w-full"
          >
            <X className="h-4 w-4 mr-2" />
            Clear Filters
          </Button>
        )}
      </div>
    </div>
  );
}

interface DateRangePickerProps {
  dateRange: { start: Date; end: Date } | null;
  onDateRangeChange: (range: { start: Date; end: Date } | null) => void;
}

function DateRangePicker({ dateRange, onDateRangeChange }: DateRangePickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [tempStart, setTempStart] = useState<Date | undefined>(
    dateRange?.start
  );
  const [tempEnd, setTempEnd] = useState<Date | undefined>(dateRange?.end);

  const handleApply = () => {
    if (tempStart && tempEnd) {
      onDateRangeChange({ start: tempStart, end: tempEnd });
      setIsOpen(false);
    }
  };

  const handleClear = () => {
    setTempStart(undefined);
    setTempEnd(undefined);
    onDateRangeChange(null);
    setIsOpen(false);
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            'w-full justify-start text-left font-normal',
            !dateRange && 'text-muted-foreground'
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {dateRange ? (
            <>
              {format(dateRange.start, 'MMM d, yyyy')} -{' '}
              {format(dateRange.end, 'MMM d, yyyy')}
            </>
          ) : (
            <span>Pick a date range</span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <div className="p-3 space-y-3">
          <div>
            <Label className="text-xs text-muted-foreground mb-2 block">
              Start Date
            </Label>
            <Calendar
              mode="single"
              selected={tempStart}
              onSelect={setTempStart}
              initialFocus
            />
          </div>
          <div>
            <Label className="text-xs text-muted-foreground mb-2 block">
              End Date
            </Label>
            <Calendar
              mode="single"
              selected={tempEnd}
              onSelect={setTempEnd}
              disabled={(date) => (tempStart ? date < tempStart : false)}
            />
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={handleApply}
              disabled={!tempStart || !tempEnd}
              className="flex-1"
            >
              Apply
            </Button>
            <Button size="sm" variant="outline" onClick={handleClear} className="flex-1">
              Clear
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

import { useState, useEffect } from 'react';
