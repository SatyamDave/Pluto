import React from 'react';
import { Button, Card, Row, Col, Typography, Space, Statistic } from 'antd';
import { ArrowRightOutlined, TrophyOutlined, RocketOutlined, CrownOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const { Title, Paragraph } = Typography;

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const features = [
    {
      icon: <TrophyOutlined style={{ fontSize: '2rem', color: '#1890ff' }} />,
      title: 'AI-Powered Trading',
      description: 'Advanced algorithms and machine learning for optimal trading strategies'
    },
    {
      icon: <RocketOutlined style={{ fontSize: '2rem', color: '#52c41a' }} />,
      title: 'Real-time Analytics',
      description: 'Live market data, backtesting, and performance metrics'
    },
    {
      icon: <CrownOutlined style={{ fontSize: '2rem', color: '#faad14' }} />,
      title: 'Multi-tier Access',
      description: 'From beginner to enterprise, scale with your trading needs'
    }
  ];

  const pricingTiers = [
    {
      name: 'Learner',
      price: 'Free',
      features: [
        'Paper trading only',
        'Basic AI tutor',
        '5 backtests per month',
        'Community support'
      ],
      buttonText: 'Get Started Free',
      popular: false
    },
    {
      name: 'Pro',
      price: '$29/month',
      features: [
        'Live trading access',
        'Advanced AI strategies',
        'Unlimited backtests',
        'Priority support',
        'Real-time alerts'
      ],
      buttonText: 'Start Pro Trial',
      popular: true
    },
    {
      name: 'Quant',
      price: '$99/month',
      features: [
        'Everything in Pro',
        'Custom strategy builder',
        'API access',
        'Advanced analytics',
        'White-label options'
      ],
      buttonText: 'Start Quant Trial',
      popular: false
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      features: [
        'Everything in Quant',
        'Dedicated support',
        'Custom integrations',
        'Team management',
        'SLA guarantees'
      ],
      buttonText: 'Contact Sales',
      popular: false
    }
  ];

  return (
    <div style={{ minHeight: '100vh' }}>
      {/* Hero Section */}
      <div style={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '80px 0',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px' }}>
          <Title level={1} style={{ color: 'white', marginBottom: 24 }}>
            Your AI Market Terminal
          </Title>
          <Paragraph style={{ fontSize: '1.2rem', marginBottom: 40, opacity: 0.9 }}>
            Advanced trading algorithms powered by artificial intelligence. 
            From paper trading to live execution, scale your trading with confidence.
          </Paragraph>
          <Space size="large">
            <Button 
              type="primary" 
              size="large" 
              onClick={() => navigate('/signup')}
              style={{ height: 48, padding: '0 32px' }}
            >
              Sign Up Free (Learner)
              <ArrowRightOutlined />
            </Button>
            <Button 
              size="large" 
              onClick={() => navigate('/pricing')}
              style={{ height: 48, padding: '0 32px', color: 'white', borderColor: 'white' }}
            >
              View Pricing
            </Button>
          </Space>
        </div>
      </div>

      {/* Features Section */}
      <div style={{ padding: '80px 0', background: '#fafafa' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px' }}>
          <Title level={2} style={{ textAlign: 'center', marginBottom: 60 }}>
            Why Choose AI Market Terminal?
          </Title>
          <Row gutter={[32, 32]}>
            {features.map((feature, index) => (
              <Col xs={24} md={8} key={index}>
                <Card style={{ textAlign: 'center', height: '100%' }}>
                  <div style={{ marginBottom: 16 }}>
                    {feature.icon}
                  </div>
                  <Title level={4}>{feature.title}</Title>
                  <Paragraph>{feature.description}</Paragraph>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </div>

      {/* Stats Section */}
      <div style={{ padding: '60px 0', background: 'white' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px' }}>
          <Row gutter={[32, 32]} justify="center">
            <Col xs={12} md={6}>
              <Statistic title="Active Traders" value={10000} suffix="+" />
            </Col>
            <Col xs={12} md={6}>
              <Statistic title="Backtests Run" value={500000} suffix="+" />
            </Col>
            <Col xs={12} md={6}>
              <Statistic title="Trading Pairs" value={100} suffix="+" />
            </Col>
            <Col xs={12} md={6}>
              <Statistic title="Success Rate" value={85} suffix="%" />
            </Col>
          </Row>
        </div>
      </div>

      {/* Pricing Section */}
      <div style={{ padding: '80px 0', background: '#fafafa' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px' }}>
          <Title level={2} style={{ textAlign: 'center', marginBottom: 60 }}>
            Choose Your Plan
          </Title>
          <Row gutter={[24, 24]}>
            {pricingTiers.map((tier, index) => (
              <Col xs={24} sm={12} lg={6} key={index}>
                <Card 
                  style={{ 
                    textAlign: 'center', 
                    height: '100%',
                    border: tier.popular ? '2px solid #1890ff' : undefined,
                    position: 'relative'
                  }}
                >
                  {tier.popular && (
                    <div style={{
                      position: 'absolute',
                      top: -12,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      background: '#1890ff',
                      color: 'white',
                      padding: '4px 16px',
                      borderRadius: 12,
                      fontSize: '0.8rem',
                      fontWeight: 'bold'
                    }}>
                      MOST POPULAR
                    </div>
                  )}
                  <Title level={3}>{tier.name}</Title>
                  <Title level={2} style={{ color: '#1890ff' }}>
                    {tier.price}
                  </Title>
                  <ul style={{ listStyle: 'none', padding: 0, margin: '24px 0' }}>
                    {tier.features.map((feature, featureIndex) => (
                      <li key={featureIndex} style={{ margin: '8px 0' }}>
                        ✓ {feature}
                      </li>
                    ))}
                  </ul>
                  <Button 
                    type={tier.popular ? 'primary' : 'default'}
                    size="large"
                    block
                    onClick={() => {
                      if (tier.name === 'Enterprise') {
                        window.open('mailto:sales@aimarketterminal.com', '_blank');
                      } else {
                        navigate('/signup');
                      }
                    }}
                  >
                    {tier.buttonText}
                  </Button>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </div>

      {/* CTA Section */}
      <div style={{ 
        background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
        color: 'white',
        padding: '60px 0',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto', padding: '0 24px' }}>
          <Title level={2} style={{ color: 'white', marginBottom: 24 }}>
            Ready to Start Trading?
          </Title>
          <Paragraph style={{ fontSize: '1.1rem', marginBottom: 32, opacity: 0.9 }}>
            Join thousands of traders who are already using AI Market Terminal to improve their trading performance.
          </Paragraph>
          <Button 
            type="primary" 
            size="large" 
            onClick={() => navigate('/signup')}
            style={{ 
              height: 48, 
              padding: '0 32px',
              background: 'white',
              color: '#1890ff',
              border: 'none'
            }}
          >
            Get Started Now
            <ArrowRightOutlined />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
