import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Typography, 
  Row, 
  Col, 
  Statistic, 
  Progress, 
  Table, 
  Tag, 
  Space, 
  Button,
  DatePicker,
  Select,
  Alert,
  Divider,
  Badge
} from 'antd';
import { 
  UserOutlined, 
  DollarOutlined, 
  TrophyOutlined,
  TrendingUpOutlined,
  TrendingDownOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  DownloadOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import posthog from 'posthog-js';

const { Title, Paragraph, Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

interface PMFMetrics {
  dau: number;
  wau: number;
  mau: number;
  dauMauRatio: number;
  conversionRate: number;
  npsScore: number;
  churnRate: number;
  arpu: number;
  ltv: number;
  referralRate: number;
}

interface CohortData {
  cohort: string;
  size: number;
  conversionRate: number;
  retention: number;
  revenue: number;
}

interface FeatureUsage {
  feature: string;
  usage: number;
  satisfaction: number;
  revenueCorrelation: number;
}

const PMFDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<PMFMetrics | null>(null);
  const [cohorts, setCohorts] = useState<CohortData[]>([]);
  const [featureUsage, setFeatureUsage] = useState<FeatureUsage[]>([]);
  const [dateRange, setDateRange] = useState<[string, string]>(['2024-12-01', '2024-12-31']);
  const [loading, setLoading] = useState(true);

  // Mock data for demonstration
  const mockMetrics: PMFMetrics = {
    dau: 145,
    wau: 892,
    mau: 2340,
    dauMauRatio: 0.062, // 6.2%
    conversionRate: 0.18, // 18%
    npsScore: 52,
    churnRate: 0.08, // 8%
    arpu: 45.50,
    ltv: 342.00,
    referralRate: 0.23 // 23%
  };

  const mockCohorts: CohortData[] = [
    { cohort: 'Week 1', size: 200, conversionRate: 0.15, retention: 0.85, revenue: 1350 },
    { cohort: 'Week 2', size: 180, conversionRate: 0.18, retention: 0.82, revenue: 1458 },
    { cohort: 'Week 3', size: 165, conversionRate: 0.21, retention: 0.79, revenue: 1386 },
    { cohort: 'Week 4', size: 142, conversionRate: 0.19, retention: 0.76, revenue: 1075 }
  ];

  const mockFeatureUsage: FeatureUsage[] = [
    { feature: 'AI Tutor', usage: 0.89, satisfaction: 4.2, revenueCorrelation: 0.78 },
    { feature: 'Backtesting', usage: 0.67, satisfaction: 4.1, revenueCorrelation: 0.85 },
    { feature: 'Paper Trading', usage: 0.92, satisfaction: 4.3, revenueCorrelation: 0.65 },
    { feature: 'Live Trading', usage: 0.34, satisfaction: 3.9, revenueCorrelation: 0.92 },
    { feature: 'Market Analysis', usage: 0.76, satisfaction: 4.0, revenueCorrelation: 0.71 }
  ];

  useEffect(() => {
    fetchPMFData();
  }, [dateRange]);

  const fetchPMFData = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from your analytics API
      const response = await fetch(`/api/pmf/metrics?start=${dateRange[0]}&end=${dateRange[1]}`);
      if (response.ok) {
        const data = await response.json();
        setMetrics(data.metrics);
        setCohorts(data.cohorts);
        setFeatureUsage(data.featureUsage);
      } else {
        // Use mock data for demonstration
        setMetrics(mockMetrics);
        setCohorts(mockCohorts);
        setFeatureUsage(mockFeatureUsage);
      }
    } catch (error) {
      console.error('Failed to fetch PMF data:', error);
      // Use mock data as fallback
      setMetrics(mockMetrics);
      setCohorts(mockCohorts);
      setFeatureUsage(mockFeatureUsage);
    } finally {
      setLoading(false);
    }
  };

  const getPMFStatus = () => {
    if (!metrics) return 'unknown';
    
    const { dauMauRatio, conversionRate, npsScore } = metrics;
    
    if (dauMauRatio > 0.4 && conversionRate > 0.15 && npsScore > 50) {
      return 'green';
    } else if (dauMauRatio > 0.3 && conversionRate > 0.05 && npsScore > 20) {
      return 'yellow';
    } else {
      return 'red';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'green':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 24 }} />;
      case 'yellow':
        return <ExclamationCircleOutlined style={{ color: '#faad14', fontSize: 24 }} />;
      case 'red':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 24 }} />;
      default:
        return <ExclamationCircleOutlined style={{ color: '#d9d9d9', fontSize: 24 }} />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'green':
        return 'Strong PMF - Ready to Scale';
      case 'yellow':
        return 'Moderate PMF - Needs Iteration';
      case 'red':
        return 'Weak PMF - Major Changes Needed';
      default:
        return 'Unknown PMF Status';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'green':
        return '#52c41a';
      case 'yellow':
        return '#faad14';
      case 'red':
        return '#ff4d4f';
      default:
        return '#d9d9d9';
    }
  };

  const exportReport = () => {
    const reportData = {
      metrics,
      cohorts,
      featureUsage,
      dateRange,
      pmfStatus: getPMFStatus(),
      generatedAt: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pmf-report-${dateRange[0]}-${dateRange[1]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    posthog.capture('pmf_report_exported', {
      dateRange,
      pmfStatus: getPMFStatus()
    });
  };

  const cohortColumns = [
    {
      title: 'Cohort',
      dataIndex: 'cohort',
      key: 'cohort',
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size',
      render: (value: number) => value.toLocaleString(),
    },
    {
      title: 'Conversion Rate',
      dataIndex: 'conversionRate',
      key: 'conversionRate',
      render: (value: number) => `${(value * 100).toFixed(1)}%`,
    },
    {
      title: 'Retention',
      dataIndex: 'retention',
      key: 'retention',
      render: (value: number) => `${(value * 100).toFixed(1)}%`,
    },
    {
      title: 'Revenue',
      dataIndex: 'revenue',
      key: 'revenue',
      render: (value: number) => `$${value.toLocaleString()}`,
    },
  ];

  const featureColumns = [
    {
      title: 'Feature',
      dataIndex: 'feature',
      key: 'feature',
    },
    {
      title: 'Usage Rate',
      dataIndex: 'usage',
      key: 'usage',
      render: (value: number) => `${(value * 100).toFixed(1)}%`,
    },
    {
      title: 'Satisfaction',
      dataIndex: 'satisfaction',
      key: 'satisfaction',
      render: (value: number) => `${value.toFixed(1)}/5`,
    },
    {
      title: 'Revenue Correlation',
      dataIndex: 'revenueCorrelation',
      key: 'revenueCorrelation',
      render: (value: number) => {
        const color = value > 0.8 ? 'green' : value > 0.6 ? 'orange' : 'red';
        return <Tag color={color}>{(value * 100).toFixed(0)}%</Tag>;
      },
    },
  ];

  const pmfStatus = getPMFStatus();

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2}>PMF Validation Dashboard</Title>
            <Paragraph>
              Product-Market Fit metrics and cohort analysis for AI Market Terminal beta
            </Paragraph>
          </Col>
          <Col>
            <Space>
              <RangePicker 
                value={[new Date(dateRange[0]), new Date(dateRange[1])]}
                onChange={(dates) => {
                  if (dates) {
                    setDateRange([
                      dates[0]?.toISOString().split('T')[0] || '',
                      dates[1]?.toISOString().split('T')[0] || ''
                    ]);
                  }
                }}
              />
              <Button 
                icon={<ReloadOutlined />} 
                onClick={fetchPMFData}
                loading={loading}
              >
                Refresh
              </Button>
              <Button 
                type="primary" 
                icon={<DownloadOutlined />} 
                onClick={exportReport}
              >
                Export Report
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* PMF Status Alert */}
      <Alert
        message={
          <Space>
            {getStatusIcon(pmfStatus)}
            <span style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {getStatusText(pmfStatus)}
            </span>
          </Space>
        }
        description={
          <div>
            <Paragraph style={{ marginBottom: '8px' }}>
              <strong>Current Status:</strong> {pmfStatus.toUpperCase()}
            </Paragraph>
            <Paragraph style={{ marginBottom: '0' }}>
              <strong>Criteria:</strong> DAU/MAU > 40%, Conversion > 15%, NPS > 50
            </Paragraph>
          </div>
        }
        type={pmfStatus === 'green' ? 'success' : pmfStatus === 'yellow' ? 'warning' : 'error'}
        style={{ marginBottom: '24px' }}
        showIcon={false}
      />

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="DAU/MAU Ratio"
              value={metrics?.dauMauRatio ? (metrics.dauMauRatio * 100).toFixed(1) : 0}
              suffix="%"
              valueStyle={{ 
                color: metrics?.dauMauRatio && metrics.dauMauRatio > 0.4 ? '#52c41a' : 
                       metrics?.dauMauRatio && metrics.dauMauRatio > 0.3 ? '#faad14' : '#ff4d4f'
              }}
            />
            <Progress 
              percent={metrics?.dauMauRatio ? (metrics.dauMauRatio * 100) : 0} 
              showInfo={false}
              strokeColor={getStatusColor(pmfStatus)}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Conversion Rate"
              value={metrics?.conversionRate ? (metrics.conversionRate * 100).toFixed(1) : 0}
              suffix="%"
              valueStyle={{ 
                color: metrics?.conversionRate && metrics.conversionRate > 0.15 ? '#52c41a' : 
                       metrics?.conversionRate && metrics.conversionRate > 0.05 ? '#faad14' : '#ff4d4f'
              }}
            />
            <Progress 
              percent={metrics?.conversionRate ? (metrics.conversionRate * 100) : 0} 
              showInfo={false}
              strokeColor={getStatusColor(pmfStatus)}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="NPS Score"
              value={metrics?.npsScore || 0}
              suffix="/100"
              valueStyle={{ 
                color: metrics?.npsScore && metrics.npsScore > 50 ? '#52c41a' : 
                       metrics?.npsScore && metrics.npsScore > 20 ? '#faad14' : '#ff4d4f'
              }}
            />
            <Progress 
              percent={metrics?.npsScore || 0} 
              showInfo={false}
              strokeColor={getStatusColor(pmfStatus)}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="ARPU"
              value={metrics?.arpu || 0}
              prefix="$"
              precision={2}
              valueStyle={{ color: '#1890ff' }}
            />
            <Text type="secondary">Monthly average</Text>
          </Card>
        </Col>
      </Row>

      {/* Detailed Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={12}>
          <Card title="User Metrics" extra={<UserOutlined />}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Statistic title="Daily Active Users" value={metrics?.dau || 0} />
              </Col>
              <Col span={12}>
                <Statistic title="Weekly Active Users" value={metrics?.wau || 0} />
              </Col>
              <Col span={12}>
                <Statistic title="Monthly Active Users" value={metrics?.mau || 0} />
              </Col>
              <Col span={12}>
                <Statistic 
                  title="Churn Rate" 
                  value={metrics?.churnRate ? (metrics.churnRate * 100).toFixed(1) : 0}
                  suffix="%"
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Revenue Metrics" extra={<DollarOutlined />}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Statistic 
                  title="LTV" 
                  value={metrics?.ltv || 0}
                  prefix="$"
                  precision={2}
                />
              </Col>
              <Col span={12}>
                <Statistic 
                  title="Referral Rate" 
                  value={metrics?.referralRate ? (metrics.referralRate * 100).toFixed(1) : 0}
                  suffix="%"
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Cohort Analysis */}
      <Card title="Cohort Analysis" style={{ marginBottom: '24px' }}>
        <Table 
          dataSource={cohorts} 
          columns={cohortColumns} 
          pagination={false}
          rowKey="cohort"
        />
      </Card>

      {/* Feature Usage */}
      <Card title="Feature Usage & Revenue Correlation" style={{ marginBottom: '24px' }}>
        <Table 
          dataSource={featureUsage} 
          columns={featureColumns} 
          pagination={false}
          rowKey="feature"
        />
      </Card>

      {/* Recommendations */}
      <Card title="PMF Recommendations">
        {pmfStatus === 'green' && (
          <Alert
            message="Strong Product-Market Fit Detected"
            description="Your product shows strong PMF indicators. Consider scaling your user acquisition efforts and expanding to new markets."
            type="success"
            showIcon
          />
        )}
        {pmfStatus === 'yellow' && (
          <Alert
            message="Moderate Product-Market Fit - Iteration Needed"
            description="Focus on improving user engagement and conversion rates. Consider A/B testing onboarding flows and feature improvements."
            type="warning"
            showIcon
          />
        )}
        {pmfStatus === 'red' && (
          <Alert
            message="Weak Product-Market Fit - Major Changes Required"
            description="Significant product changes are needed. Focus on understanding user needs and iterating on core value proposition."
            type="error"
            showIcon
          />
        )}
      </Card>
    </div>
  );
};

export default PMFDashboard;
