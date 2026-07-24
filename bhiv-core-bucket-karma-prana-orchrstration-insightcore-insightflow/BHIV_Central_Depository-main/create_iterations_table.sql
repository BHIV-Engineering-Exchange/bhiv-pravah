
-- Create iterations table
CREATE TABLE IF NOT EXISTS iterations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  spec_id UUID NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
  iteration_number INTEGER NOT NULL,
  changes JSONB,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Unique constraint for iteration numbers per spec
  UNIQUE(spec_id, iteration_number)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_iterations_spec_id ON iterations(spec_id);
CREATE INDEX IF NOT EXISTS idx_iterations_status ON iterations(status);
CREATE INDEX IF NOT EXISTS idx_iterations_created_at ON iterations(created_at DESC);

-- Row Level Security
ALTER TABLE iterations ENABLE ROW LEVEL SECURITY;

-- RLS Policies
DROP POLICY IF EXISTS "Users can view iterations for specs they own" ON iterations;
CREATE POLICY "Users can view iterations for specs they own" ON iterations
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM specs
      WHERE specs.id = iterations.spec_id
      AND specs.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can insert iterations for specs they own" ON iterations;
CREATE POLICY "Users can insert iterations for specs they own" ON iterations
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM specs
      WHERE specs.id = iterations.spec_id
      AND specs.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can update iterations for specs they own" ON iterations;
CREATE POLICY "Users can update iterations for specs they own" ON iterations
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM specs
      WHERE specs.id = iterations.spec_id
      AND specs.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can delete iterations for specs they own" ON iterations;
CREATE POLICY "Users can delete iterations for specs they own" ON iterations
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM specs
      WHERE specs.id = iterations.spec_id
      AND specs.user_id = auth.uid()
    )
  );
