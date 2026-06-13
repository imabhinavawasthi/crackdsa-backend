-- v1.8.0__create_payments_and_coupons_tables.sql
-- Creates tables for managing coupons and transactions

CREATE TABLE IF NOT EXISTS public.coupons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    discount_type TEXT NOT NULL CHECK (discount_type IN ('percentage', 'fixed')),
    discount_value NUMERIC NOT NULL,
    max_uses INTEGER NULL,
    used_count INTEGER DEFAULT 0,
    valid_until TIMESTAMP WITH TIME ZONE NULL,
    applicable_to JSONB DEFAULT '[]'::jsonb, -- e.g. ["PRO", "course_uuid"] or ["ALL"]
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    amount NUMERIC NOT NULL,
    currency TEXT DEFAULT 'INR',
    status TEXT NOT NULL CHECK (status IN ('pending', 'success', 'failed')),
    razorpay_order_id TEXT NULL UNIQUE,
    razorpay_payment_id TEXT NULL UNIQUE,
    razorpay_signature TEXT NULL,
    coupon_id UUID NULL REFERENCES public.coupons(id) ON DELETE SET NULL,
    purchase_type TEXT NOT NULL CHECK (purchase_type IN ('pro_subscription', 'course')),
    target_id TEXT NULL, -- course UUID or plan type ('3_months', '6_months')
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- RLS for Coupons (Public Read, Admin Write)
ALTER TABLE public.coupons ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Coupons are viewable by everyone." ON public.coupons FOR SELECT USING (true);
CREATE POLICY "Admins can insert coupons." ON public.coupons FOR INSERT WITH CHECK (
  auth.uid() IN (SELECT id FROM public.users WHERE role = 'admin')
);
CREATE POLICY "Admins can update coupons." ON public.coupons FOR UPDATE USING (
  auth.uid() IN (SELECT id FROM public.users WHERE role = 'admin')
);

-- RLS for Transactions (Users can view their own, Admins view all)
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own transactions." ON public.transactions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Admins can view all transactions." ON public.transactions FOR SELECT USING (
  auth.uid() IN (SELECT id FROM public.users WHERE role = 'admin')
);
-- We don't allow users to insert/update transactions directly via REST; it will be handled by the backend service.
