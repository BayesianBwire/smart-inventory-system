-- ==========================================
-- RahaSoft ERP - Supabase RLS Policies
-- Row Level Security for Multi-Tenant SaaS
-- ==========================================

-- Enable RLS on all tables
-- This ensures data isolation between companies

-- ==========================================
-- Core Tables RLS Policies
-- ==========================================

-- Companies table
ALTER TABLE company ENABLE ROW LEVEL SECURITY;

-- Company founders and admins can see their own company
CREATE POLICY "Users can view their own company" ON company
    FOR SELECT USING (
        id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid() 
            AND role IN ('founder', 'admin')
        )
    );

-- Only founders can update their company
CREATE POLICY "Founders can update their company" ON company
    FOR UPDATE USING (
        id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid() 
            AND role = 'founder'
        )
    );

-- New companies can be inserted (for registration)
CREATE POLICY "Allow company registration" ON company
    FOR INSERT WITH CHECK (true);

-- ==========================================
-- Users table
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;

-- Users can see other users in their company
CREATE POLICY "Users can view company members" ON "user"
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON "user"
    FOR UPDATE USING (id = auth.uid());

-- Admins and founders can update users in their company
CREATE POLICY "Admins can manage company users" ON "user"
    FOR UPDATE USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid() 
            AND role IN ('founder', 'admin')
        )
    );

-- Allow user registration
CREATE POLICY "Allow user registration" ON "user"
    FOR INSERT WITH CHECK (true);

-- ==========================================
-- Products and Inventory
-- ==========================================

ALTER TABLE product ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company products" ON product
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Stock movements
ALTER TABLE stock_movement ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company stock movements" ON stock_movement
    FOR ALL USING (
        product_id IN (
            SELECT id FROM product 
            WHERE company_id IN (
                SELECT company_id FROM "user" 
                WHERE id = auth.uid()
            )
        )
    );

-- Categories
ALTER TABLE category ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company categories" ON category
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Suppliers
ALTER TABLE supplier ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company suppliers" ON supplier
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- ==========================================
-- Sales and Finance
-- ==========================================

ALTER TABLE sale ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company sales" ON sale
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Chart of Accounts
ALTER TABLE chart_of_accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company chart of accounts" ON chart_of_accounts
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Invoices
ALTER TABLE invoice ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company invoices" ON invoice
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Invoice Items
ALTER TABLE invoice_item ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company invoice items" ON invoice_item
    FOR ALL USING (
        invoice_id IN (
            SELECT id FROM invoice 
            WHERE company_id IN (
                SELECT company_id FROM "user" 
                WHERE id = auth.uid()
            )
        )
    );

-- Payments
ALTER TABLE payment ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company payments" ON payment
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Expenses
ALTER TABLE expense ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company expenses" ON expense
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- ==========================================
-- HR and Payroll
-- ==========================================

ALTER TABLE employee ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company employees" ON employee
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Payroll
ALTER TABLE payroll ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company payroll" ON payroll
    FOR ALL USING (
        employee_id IN (
            SELECT id FROM employee 
            WHERE company_id IN (
                SELECT company_id FROM "user" 
                WHERE id = auth.uid()
            )
        )
    );

-- ==========================================
-- CRM
-- ==========================================

-- Leads
ALTER TABLE lead ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company leads" ON lead
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Customers
ALTER TABLE customer ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company customers" ON customer
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Opportunities
ALTER TABLE opportunity ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company opportunities" ON opportunity
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- CRM Activities
ALTER TABLE crm_activity ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company crm activities" ON crm_activity
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- ==========================================
-- Security and Enterprise Features
-- ==========================================

-- Two Factor Auth
ALTER TABLE two_factor_auth ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own 2FA" ON two_factor_auth
    FOR ALL USING (user_id = auth.uid());

-- API Keys
ALTER TABLE api_key ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company API keys" ON api_key
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid() 
            AND role IN ('founder', 'admin')
        )
    );

-- Webhooks
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company webhooks" ON webhooks
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid() 
            AND role IN ('founder', 'admin')
        )
    );

-- Login Attempts
ALTER TABLE login_attempt ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own login attempts" ON login_attempt
    FOR SELECT USING (user_id = auth.uid());

-- Admins can view all company login attempts
CREATE POLICY "Admins can view company login attempts" ON login_attempt
    FOR SELECT USING (
        user_id IN (
            SELECT id FROM "user" 
            WHERE company_id IN (
                SELECT company_id FROM "user" 
                WHERE id = auth.uid() 
                AND role IN ('founder', 'admin')
            )
        )
    );

-- ==========================================
-- Business Intelligence
-- ==========================================

-- Dashboards
ALTER TABLE dashboard ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company dashboards" ON dashboard
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Dashboard Widgets
ALTER TABLE dashboard_widget ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company dashboard widgets" ON dashboard_widget
    FOR ALL USING (
        dashboard_id IN (
            SELECT id FROM dashboard 
            WHERE company_id IN (
                SELECT company_id FROM "user" 
                WHERE id = auth.uid()
            )
        )
    );

-- Reports
ALTER TABLE report ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company reports" ON report
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- KPI Definitions
ALTER TABLE kpi_definitions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company KPIs" ON kpi_definitions
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- KPI Values
ALTER TABLE kpi_values ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company KPI values" ON kpi_values
    FOR ALL USING (
        kpi_id IN (
            SELECT id FROM kpi_definitions 
            WHERE company_id IN (
                SELECT company_id FROM "user" 
                WHERE id = auth.uid()
            )
        )
    );

-- ==========================================
-- Workflow & Automation
-- ==========================================

-- Workflow Templates
ALTER TABLE workflow_templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company workflow templates" ON workflow_templates
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Workflows
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company workflows" ON workflows
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- Workflow Tasks
ALTER TABLE workflow_tasks ENABLE ROW LEVEL SECURITY;

-- Users can view tasks in their company workflows or assigned to them
CREATE POLICY "Users can view relevant workflow tasks" ON workflow_tasks
    FOR ALL USING (
        workflow_id IN (
            SELECT id FROM workflows 
            WHERE company_id IN (
                SELECT company_id FROM "user" 
                WHERE id = auth.uid()
            )
        ) OR assigned_to = auth.uid()
    );

-- Workflow Actions
ALTER TABLE workflow_actions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view workflow actions" ON workflow_actions
    FOR ALL USING (
        task_id IN (
            SELECT id FROM workflow_tasks 
            WHERE workflow_id IN (
                SELECT id FROM workflows 
                WHERE company_id IN (
                    SELECT company_id FROM "user" 
                    WHERE id = auth.uid()
                )
            )
        )
    );

-- Process Automations
ALTER TABLE process_automations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company process automations" ON process_automations
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid()
        )
    );

-- ==========================================
-- Audit and Logging
-- ==========================================

-- Audit Log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view company audit logs" ON audit_log
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM "user" 
            WHERE id = auth.uid() 
            AND role IN ('founder', 'admin')
        )
    );

-- Login Log
ALTER TABLE login_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own login logs" ON login_log
    FOR SELECT USING (user_id = auth.uid());

-- Admins can view all company login logs
CREATE POLICY "Admins can view company login logs" ON login_log
    FOR SELECT USING (
        user_id IN (
            SELECT id FROM "user" 
            WHERE company_id IN (
                SELECT company_id FROM "user" 
                WHERE id = auth.uid() 
                AND role IN ('founder', 'admin')
            )
        )
    );

-- ==========================================
-- Utility Functions for RLS
-- ==========================================

-- Function to get current user's company_id
CREATE OR REPLACE FUNCTION get_user_company_id()
RETURNS UUID AS $$
BEGIN
    RETURN (
        SELECT company_id 
        FROM "user" 
        WHERE id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user is admin/founder
CREATE OR REPLACE FUNCTION is_admin_or_founder()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN (
        SELECT role IN ('founder', 'admin')
        FROM "user" 
        WHERE id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user belongs to company
CREATE OR REPLACE FUNCTION user_belongs_to_company(target_company_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN (
        SELECT EXISTS(
            SELECT 1 FROM "user" 
            WHERE id = auth.uid() 
            AND company_id = target_company_id
        )
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ==========================================
-- Performance Indexes for RLS
-- ==========================================

-- Create indexes to optimize RLS policy performance
CREATE INDEX IF NOT EXISTS idx_user_company_id ON "user"(company_id);
CREATE INDEX IF NOT EXISTS idx_user_id_company_id ON "user"(id, company_id);
CREATE INDEX IF NOT EXISTS idx_user_role_company_id ON "user"(role, company_id);

CREATE INDEX IF NOT EXISTS idx_product_company_id ON product(company_id);
CREATE INDEX IF NOT EXISTS idx_sale_company_id ON sale(company_id);
CREATE INDEX IF NOT EXISTS idx_invoice_company_id ON invoice(company_id);
CREATE INDEX IF NOT EXISTS idx_employee_company_id ON employee(company_id);
CREATE INDEX IF NOT EXISTS idx_lead_company_id ON lead(company_id);
CREATE INDEX IF NOT EXISTS idx_workflows_company_id ON workflows(company_id);
CREATE INDEX IF NOT EXISTS idx_workflow_tasks_assigned_to ON workflow_tasks(assigned_to);

-- ==========================================
-- Data Migration for Existing Records
-- ==========================================

-- If you have existing data without proper company associations,
-- you may need to run migration scripts here.
-- This is just an example - adjust based on your actual data.

-- Update any records that might be missing company_id references
-- UPDATE product SET company_id = (SELECT id FROM company LIMIT 1) WHERE company_id IS NULL;
-- UPDATE sale SET company_id = (SELECT id FROM company LIMIT 1) WHERE company_id IS NULL;

-- ==========================================
-- Testing RLS Policies
-- ==========================================

-- You can test RLS policies by running queries as different users
-- Example testing queries (run these after setting up test users):

/*
-- Test as a regular user
SET ROLE TO regular_user_role;
SELECT * FROM product; -- Should only see products from user's company

-- Test as admin
SET ROLE TO admin_user_role;
SELECT * FROM audit_log; -- Should see all audit logs for company

-- Reset to superuser
RESET ROLE;
*/

-- ==========================================
-- Notes for Implementation
-- ==========================================

/*
1. Replace auth.uid() with your actual authentication user ID function
2. Adjust UUID types to match your actual ID types (might be INTEGER)
3. Test all policies thoroughly before deploying to production
4. Monitor performance impact of RLS policies
5. Consider creating more granular policies for specific use cases
6. Ensure your application properly sets the authentication context
7. Add specific policies for soft deletes if you use them
8. Consider adding policies for bulk operations
*/

-- ==========================================
-- Supabase Specific Configuration
-- ==========================================

-- Enable real-time for specific tables (optional)
-- ALTER PUBLICATION supabase_realtime ADD TABLE workflows;
-- ALTER PUBLICATION supabase_realtime ADD TABLE workflow_tasks;
-- ALTER PUBLICATION supabase_realtime ADD TABLE dashboard;

-- Set up Supabase auth integration
-- Ensure your authentication flow properly sets the user context
-- You may need to create a trigger to sync auth.users with your user table
