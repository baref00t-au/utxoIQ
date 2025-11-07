'use client';

import { SignalType } from '@/types';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Search } from 'lucide-react';

interface InsightFiltersProps {
  selectedCategory: SignalType | 'all';
  onCategoryChange: (category: SignalType | 'all') => void;
  highConfidenceOnly: boolean;
  onHighConfidenceChange: (value: boolean) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export function InsightFilters({
  selectedCategory,
  onCategoryChange,
  highConfidenceOnly,
  onHighConfidenceChange,
  searchQuery,
  onSearchChange,
}: InsightFiltersProps) {
  return (
    <div className="space-y-6 rounded-2xl border border-border bg-card p-6">
      <div>
        <Label htmlFor="search" className="text-sm font-medium mb-2 block">
          Search
        </Label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            id="search"
            type="text"
            placeholder="Search insights..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      <div>
        <Label className="text-sm font-medium mb-3 block">Category</Label>
        <Tabs
          value={selectedCategory}
          onValueChange={(value) => onCategoryChange(value as SignalType | 'all')}
          className="w-full"
        >
          <TabsList className="grid w-full grid-cols-2 gap-2">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="mempool">Mempool</TabsTrigger>
            <TabsTrigger value="exchange">Exchange</TabsTrigger>
            <TabsTrigger value="miner">Miner</TabsTrigger>
            <TabsTrigger value="whale">Whale</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="flex items-center justify-between">
        <Label htmlFor="high-confidence" className="text-sm font-medium">
          High confidence only (≥70%)
        </Label>
        <Switch
          id="high-confidence"
          checked={highConfidenceOnly}
          onCheckedChange={onHighConfidenceChange}
        />
      </div>
    </div>
  );
}
