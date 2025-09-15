ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own data" ON users
    FOR ALL
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id AND email = auth.email());
