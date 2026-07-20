import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  FileText,
  Edit,
  Trash2,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Landmark,
  Wallet,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  PageHeader,
  Card,
  Button,
  Input,
  Modal,
  Select,
  Loading,
  EmptyState,
} from '../../components/common';
import api from '../../services/api';
import { formatCurrency } from '../../utils/formatters';

const ChartOfAccounts = () => {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedGroups, setExpandedGroups] = useState(['Assets', 'Liabilities', 'Equity', 'Income', 'Expense']);
  const [showModal, setShowModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    code: '',
    name: '',
    type: '',
    parentAccount: '',
    description: '',
  });

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const [accountsRes, balancesRes] = await Promise.all([
        api.get('/accounts'),
        api.get('/ledger/balances').catch(() => ({ data: { data: [] } }))
      ]);
      
      const accountsList = accountsRes.data.data || [];
      const balancesList = balancesRes.data.data || [];
      
      // Create balance map
      const balanceMap = {};
      balancesList.forEach(b => {
        balanceMap[b.account || b.accountCode] = parseFloat(b.balance || 0);
      });
      
      // Merge accounts with balances
      const accountsWithBalances = accountsList.map(account => ({
        ...account,
        balance: balanceMap[account._id] || balanceMap[account.code] || 0
      }));
      
      setAccounts(accountsWithBalances);
    } catch (error) {
      console.error('Failed to fetch accounts:', error);
      setAccounts([]);
    } finally {
      setLoading(false);
    }
  };

  const accountTypes = [
    { value: 'Assets', label: 'Assets', icon: Wallet, color: 'blue' },
    { value: 'Liabilities', label: 'Liabilities', icon: TrendingDown, color: 'red' },
    { value: 'Equity', label: 'Equity', icon: Landmark, color: 'purple' },
    { value: 'Income', label: 'Income', icon: TrendingUp, color: 'green' },
    { value: 'Expense', label: 'Expense', icon: DollarSign, color: 'orange' },
  ];

  const getTypeIcon = (type) => {
    const typeConfig = accountTypes.find((t) => t.value === type);
    return typeConfig?.icon || FileText;
  };

  const getTypeColor = (type) => {
    const colors = {
      Assets: 'text-blue-600 bg-blue-100',
      Liabilities: 'text-red-600 bg-red-100',
      Equity: 'text-purple-600 bg-purple-100',
      Income: 'text-green-600 bg-green-100',
      Expense: 'text-orange-600 bg-orange-100',
    };
    return colors[type] || 'text-muted-foreground bg-muted';
  };

  const toggleGroup = (group) => {
    setExpandedGroups((prev) =>
      prev.includes(group) ? prev.filter((g) => g !== group) : [...prev, group]
    );
  };

  const groupedAccounts = accountTypes.map((type) => ({
    ...type,
    accounts: accounts.filter((a) => a.type === type.value && !a.parentAccount),
    total: accounts
      .filter((a) => a.type === type.value)
      .reduce((sum, a) => sum + parseFloat(a.balance || 0), 0),
  }));

  const filteredGroups = groupedAccounts.map((group) => ({
    ...group,
    accounts: group.accounts.filter(
      (a) =>
        a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.code.includes(searchQuery)
    ),
  }));

  const handleOpenModal = (account = null) => {
    if (account) {
      setEditingAccount(account);
      setFormData({
        code: account.code,
        name: account.name,
        type: account.type,
        parentAccount: account.parentAccount || '',
        description: account.description || '',
      });
    } else {
      setEditingAccount(null);
      setFormData({
        code: '',
        name: '',
        type: '',
        parentAccount: '',
        description: '',
      });
    }
    setShowModal(true);
  };

  const handleSaveAccount = async () => {
    if (!formData.code || !formData.name || !formData.type) {
      toast.error('Please fill in all required fields');
      return;
    }

    setSaving(true);
    try {
      if (editingAccount) {
        await api.put(`/accounts/${editingAccount._id}`, formData);
        toast.success('Account updated successfully');
      } else {
        await api.post('/accounts', formData);
        toast.success('Account created successfully');
      }
      fetchAccounts();
      setShowModal(false);
    } catch (error) {
      toast.error(error.response?.data?.message || 'Failed to save account');
    } finally {
      setSaving(false);
    }
  };

  const getChildAccounts = (parentId) => {
    return accounts.filter((a) => a.parentAccount === parentId);
  };

  if (loading) {
    return <Loading.Page />;
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <PageHeader
        title="Chart of Accounts"
        description="Manage your account structure and balances"
        action={
          <Button onClick={() => handleOpenModal()} icon={Plus}>
            Add Account
          </Button>
        }
      />

      {/* Search */}
      <Card className="p-4">
        <Input
          placeholder="Search accounts by name or code..."
          icon={Search}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </Card>

      {/* Account Groups */}
      <div className="space-y-4">
        {filteredGroups.map((group) => (
          <Card key={group.value} padding={false}>
            {/* Group Header */}
            <button
              onClick={() => toggleGroup(group.value)}
              className="w-full flex items-center justify-between p-4 hover:bg-muted transition-colors"
            >
              <div className="flex items-center gap-3">
                {expandedGroups.includes(group.value) ? (
                  <ChevronDown className="w-5 h-5 text-muted-foreground" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-muted-foreground" />
                )}
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${getTypeColor(group.value)}`}>
                  <group.icon className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <h3 className="font-semibold text-foreground">{group.label}</h3>
                  <p className="text-sm text-muted-foreground">{group.accounts.length} accounts</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-foreground">
                  {formatCurrency(group.total)}
                </p>
              </div>
            </button>

            {/* Account List */}
            {expandedGroups.includes(group.value) && group.accounts.length > 0 && (
              <div className="border-t border-border">
                {group.accounts.map((account) => (
                  <div key={account._id}>
                    <div className="flex items-center justify-between px-4 py-3 hover:bg-muted border-b border-border/50 last:border-0">
                      <div className="flex items-center gap-3 ml-8">
                        {account.isGroup ? (
                          <FolderOpen className="w-5 h-5 text-muted-foreground" />
                        ) : (
                          <FileText className="w-5 h-5 text-muted-foreground" />
                        )}
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-mono text-muted-foreground">{account.code}</span>
                            <span className="font-medium text-foreground">{account.name}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="font-semibold text-foreground">
                          {formatCurrency(account.balance || 0)}
                        </span>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleOpenModal(account)}
                            className="p-1.5 hover:bg-muted rounded-lg"
                          >
                            <Edit className="w-4 h-4 text-muted-foreground" />
                          </button>
                        </div>
                      </div>
                    </div>
                    {/* Child Accounts */}
                    {getChildAccounts(account._id).map((child) => (
                      <div
                        key={child._id}
                        className="flex items-center justify-between px-4 py-2.5 hover:bg-muted border-b border-border/50 last:border-0 bg-muted/50"
                      >
                        <div className="flex items-center gap-3 ml-16">
                          <FileText className="w-4 h-4 text-muted-foreground" />
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-mono text-muted-foreground">{child.code}</span>
                              <span className="text-sm text-foreground">{child.name}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-sm font-medium text-foreground">
                            {formatCurrency(child.balance || 0)}
                          </span>
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleOpenModal(child)}
                              className="p-1 hover:bg-muted rounded"
                            >
                              <Edit className="w-3.5 h-3.5 text-muted-foreground" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}

            {expandedGroups.includes(group.value) && group.accounts.length === 0 && (
              <div className="p-8 text-center text-muted-foreground border-t border-border">
                No accounts in this category
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* Add/Edit Account Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={editingAccount ? 'Edit Account' : 'Add Account'}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Account Code"
              placeholder="e.g., 1100"
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value })}
              required
            />
            <Select
              label="Account Type"
              placeholder="Select type"
              options={accountTypes.map((t) => ({ value: t.value, label: t.label }))}
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              required
            />
          </div>
          <Input
            label="Account Name"
            placeholder="e.g., Bank Accounts"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <Input
            label="Description"
            placeholder="Optional description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
          <div className="flex justify-end gap-3 pt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveAccount} loading={saving}>
              {editingAccount ? 'Update' : 'Create'} Account
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default ChartOfAccounts;
