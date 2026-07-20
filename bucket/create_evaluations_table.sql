
-- Create evaluations table
CREATE TABLE IF NOT EXISTS evaluations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  spec_id UUID NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
  rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 10),
  feedback TEXT,
  evaluator_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Ensure rating is within bounds (additional check)
  CONSTRAINT rating_range_check CHECK (rating BETWEEN 1 AND 10)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_evaluations_spec_id ON evaluations(spec_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_evaluator_id ON evaluations(evaluator_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_created_at ON evaluations(created_at DESC);

-- Row Level Security
ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;

-- RLS Policies
DROP POLICY IF EXISTS "Users can view evaluations for specs they own" ON evaluations;
CREATE POLICY "Users can view evaluations for specs they own" ON evaluations
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM specs
      WHERE specs.id = evaluations.spec_id
      AND specs.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can insert evaluations for specs they own" ON evaluations;
CREATE POLICY "Users can insert evaluations for specs they own" ON evaluations
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM specs
      WHERE specs.id = evaluations.spec_id
      AND specs.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can update their own evaluations" ON evaluations;
CREATE POLICY "Users can update their own evaluations" ON evaluations
  FOR UPDATE USING (auth.uid() = evaluator_id);

DROP POLICY IF EXISTS "Users can delete their own evaluations" ON evaluations;
CREATE POLICY "Users can delete their own evaluations" ON evaluations
  FOR DELETE USING (auth.uid() = evaluator_id);
