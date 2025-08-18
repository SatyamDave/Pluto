import React, { useState } from 'react';
import { 
  Button, 
  Input, 
  Form, 
  Card, 
  Typography, 
  Space, 
  Alert, 
  Divider,
  Steps,
  Statistic,
  Row,
  Col,
  message
} from 'antd';
import { 
  MailOutlined, 
  LockOutlined, 
  CheckCircleOutlined,
  UserOutlined,
  TrophyOutlined,
  RocketOutlined,
  StarOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import posthog from 'posthog-js';

const { Title, Paragraph, Text } = Typography;
const { Step } = Steps;

interface BetaSignupForm {
  email: string;
  inviteCode?: string;
  referralCode?: string;
}

const BetaLandingPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [signupSuccess, setSignupSuccess] = useState(false);
  const [waitlistPosition, setWaitlistPosition] = useState<number | null>(null);
  const { signup } = useAuth();

  const steps = [
    {
      title: 'Join Waitlist',
      description: 'Enter your email',
      icon: <MailOutlined />
    },
    {
      title: 'Get Invite',
      description: 'Receive your code',
      icon: <LockOutlined />
    },
    {
      title: 'Start Trading',
      description: 'Access the platform',
      icon: <RocketOutlined />
    }
  ];

  const handleWaitlistSignup = async (values: { email: string }) => {
    setLoading(true);
    try {
      // Track waitlist signup
      posthog.capture('waitlist_signup', {
        email: values.email,
        timestamp: new Date().toISOString()
      });

      // Simulate API call to add to waitlist
      const response = await fetch('/api/beta/waitlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: values.email }),
      });

      if (response.ok) {
        const data = await response.json();
        setWaitlistPosition(data.position);
        setCurrentStep(1);
        message.success('You\'ve been added to the waitlist!');
        
        // Track successful waitlist signup
        posthog.capture('waitlist_signup_success', {
          email: values.email,
          position: data.position
        });
      } else {
        throw new Error('Failed to join waitlist');
      }
    } catch (error) {
      message.error('Failed to join waitlist. Please try again.');
      posthog.capture('waitlist_signup_error', {
        email: values.email,
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const handleInviteSignup = async (values: BetaSignupForm) => {
    setLoading(true);
    try {
      // Track invite signup
      posthog.capture('invite_signup', {
        email: values.email,
        hasInviteCode: !!values.inviteCode,
        hasReferralCode: !!values.referralCode
      });

      // Create account with invite code
      await signup(values.email, values.inviteCode || '', values.referralCode);
      setSignupSuccess(true);
      setCurrentStep(2);
      
      message.success('Welcome to AI Market Terminal!');
      
      // Track successful signup
      posthog.capture('beta_signup_success', {
        email: values.email,
        tier: 'learner'
      });
    } catch (error) {
      message.error('Invalid invite code or signup failed. Please try again.');
      posthog.capture('invite_signup_error', {
        email: values.email,
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReferralShare = () => {
    const referralUrl = `${window.location.origin}/beta?ref=${posthog.get_distinct_id()}`;
    navigator.clipboard.writeText(referralUrl);
    message.success('Referral link copied to clipboard!');
    
    posthog.capture('referral_link_shared', {
      referralUrl
    });
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '40px 20px'
    }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 60 }}>
          <Title level={1} style={{ color: 'white', marginBottom: 16 }}>
            🚀 AI Market Terminal
          </Title>
          <Title level={3} style={{ color: 'white', fontWeight: 300 }}>
            The Future of AI-Powered Trading
          </Title>
          <Paragraph style={{ color: 'white', fontSize: 18, marginBottom: 0 }}>
            Join the exclusive beta and be among the first to experience the next generation of trading technology
          </Paragraph>
        </div>

        {/* Beta Stats */}
        <Row gutter={[24, 24]} style={{ marginBottom: 60 }}>
          <Col xs={24} sm={8}>
            <Card style={{ textAlign: 'center', background: 'rgba(255,255,255,0.1)', border: 'none' }}>
              <Statistic 
                title={<span style={{ color: 'white' }}>Beta Users</span>}
                value={200}
                suffix={<UserOutlined style={{ color: 'white' }} />}
                valueStyle={{ color: 'white' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card style={{ textAlign: 'center', background: 'rgba(255,255,255,0.1)', border: 'none' }}>
              <Statistic 
                title={<span style={{ color: 'white' }}>Success Rate</span>}
                value={94.2}
                suffix="%" 
                valueStyle={{ color: 'white' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card style={{ textAlign: 'center', background: 'rgba(255,255,255,0.1)', border: 'none' }}>
              <Statistic 
                title={<span style={{ color: 'white' }}>Avg. Returns</span>}
                value={18.7}
                suffix="%" 
                valueStyle={{ color: 'white' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Main Content */}
        <Row gutter={[48, 48]} align="middle">
          <Col xs={24} lg={12}>
            <Card style={{ background: 'rgba(255,255,255,0.95)', borderRadius: 16 }}>
              <Steps current={currentStep} direction="vertical" size="small">
                {steps.map((step, index) => (
                  <Step 
                    key={index}
                    title={step.title}
                    description={step.description}
                    icon={step.icon}
                  />
                ))}
              </Steps>

              <Divider />

              {currentStep === 0 && (
                <div>
                  <Title level={4}>Join the Exclusive Beta</Title>
                  <Paragraph>
                    Be among the first 200 users to experience AI-powered trading. 
                    Get early access to advanced features and exclusive benefits.
                  </Paragraph>
                  
                  <Form form={form} onFinish={handleWaitlistSignup}>
                    <Form.Item
                      name="email"
                      rules={[
                        { required: true, message: 'Please enter your email' },
                        { type: 'email', message: 'Please enter a valid email' }
                      ]}
                    >
                      <Input 
                        size="large" 
                        placeholder="Enter your email address"
                        prefix={<MailOutlined />}
                      />
                    </Form.Item>
                    
                    <Button 
                      type="primary" 
                      size="large" 
                      block 
                      loading={loading}
                      htmlType="submit"
                      icon={<MailOutlined />}
                    >
                      Join Waitlist
                    </Button>
                  </Form>
                </div>
              )}

              {currentStep === 1 && (
                <div>
                  <Alert
                    message="You're on the waitlist!"
                    description={`You're position #${waitlistPosition} on our waitlist. We'll send you an invite code as soon as a spot opens up.`}
                    type="success"
                    showIcon
                    style={{ marginBottom: 24 }}
                  />
                  
                  <Title level={4}>Have an Invite Code?</Title>
                  <Paragraph>
                    If you received an invite code, you can skip the waitlist and start trading immediately.
                  </Paragraph>
                  
                  <Form form={form} onFinish={handleInviteSignup}>
                    <Form.Item
                      name="email"
                      rules={[
                        { required: true, message: 'Please enter your email' },
                        { type: 'email', message: 'Please enter a valid email' }
                      ]}
                    >
                      <Input 
                        size="large" 
                        placeholder="Enter your email address"
                        prefix={<MailOutlined />}
                      />
                    </Form.Item>
                    
                    <Form.Item
                      name="inviteCode"
                      rules={[
                        { required: true, message: 'Please enter your invite code' }
                      ]}
                    >
                      <Input 
                        size="large" 
                        placeholder="Enter your invite code"
                        prefix={<LockOutlined />}
                      />
                    </Form.Item>
                    
                    <Form.Item name="referralCode">
                      <Input 
                        size="large" 
                        placeholder="Referral code (optional)"
                        prefix={<UserOutlined />}
                      />
                    </Form.Item>
                    
                    <Button 
                      type="primary" 
                      size="large" 
                      block 
                      loading={loading}
                      htmlType="submit"
                      icon={<CheckCircleOutlined />}
                    >
                      Start Trading
                    </Button>
                  </Form>
                </div>
              )}

              {currentStep === 2 && signupSuccess && (
                <div style={{ textAlign: 'center' }}>
                  <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a', marginBottom: 24 }} />
                  <Title level={3}>Welcome to AI Market Terminal!</Title>
                  <Paragraph>
                    Your account has been created successfully. You now have access to the beta platform.
                  </Paragraph>
                  
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    <Button 
                      type="primary" 
                      size="large" 
                      block
                      href="/dashboard"
                      icon={<RocketOutlined />}
                    >
                      Go to Dashboard
                    </Button>
                    
                    <Button 
                      size="large" 
                      block
                      onClick={handleReferralShare}
                      icon={<UserOutlined />}
                    >
                      Share with Friends
                    </Button>
                  </Space>
                </div>
              )}
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <div style={{ color: 'white' }}>
              <Title level={2} style={{ color: 'white', marginBottom: 32 }}>
                Why Join the Beta?
              </Title>
              
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div>
                  <Title level={4} style={{ color: 'white' }}>
                    <StarOutlined /> Early Access Benefits
                  </Title>
                  <Paragraph style={{ color: 'white', opacity: 0.9 }}>
                    • 30-day free trial of Pro features<br/>
                    • Exclusive beta tester badge<br/>
                    • Direct feedback channel to developers<br/>
                    • Priority support and updates
                  </Paragraph>
                </div>
                
                <div>
                  <Title level={4} style={{ color: 'white' }}>
                    <TrophyOutlined /> Beta Features
                  </Title>
                  <Paragraph style={{ color: 'white', opacity: 0.9 }}>
                    • AI-powered trading strategies<br/>
                    • Real-time market analysis<br/>
                    • Advanced backtesting engine<br/>
                    • Paper and live trading
                  </Paragraph>
                </div>
                
                <div>
                  <Title level={4} style={{ color: 'white' }}>
                    <RocketOutlined /> Limited Availability
                  </Title>
                  <Paragraph style={{ color: 'white', opacity: 0.9 }}>
                    Only 200 spots available for the initial beta. 
                    Join now to secure your place and shape the future of trading.
                  </Paragraph>
                </div>
              </Space>
            </div>
          </Col>
        </Row>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: 80, color: 'white', opacity: 0.8 }}>
          <Paragraph>
            © 2024 AI Market Terminal. All rights reserved.
          </Paragraph>
        </div>
      </div>
    </div>
  );
};

export default BetaLandingPage;
