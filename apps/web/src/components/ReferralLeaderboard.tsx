import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Typography, 
  Table, 
  Avatar, 
  Tag, 
  Button, 
  Space, 
  Row, 
  Col, 
  Statistic,
  Progress,
  Modal,
  message,
  Tooltip
} from 'antd';
import { 
  TrophyOutlined, 
  UserOutlined, 
  GiftOutlined,
  ShareAltOutlined,
  CrownOutlined,
  StarOutlined,
  FireOutlined
} from '@ant-design/icons';
import posthog from 'posthog-js';

const { Title, Paragraph, Text } = Typography;

interface ReferralUser {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  totalReferrals: number;
  successfulReferrals: number;
  conversionRate: number;
  rewards: Reward[];
  rank: number;
  tier: 'bronze' | 'silver' | 'gold' | 'platinum';
}

interface Reward {
  id: string;
  type: 'ai_credits' | 'premium_trial' | 'feature_unlock' | 'badge';
  name: string;
  description: string;
  value: number;
  earnedAt: string;
  claimed: boolean;
}

const ReferralLeaderboard: React.FC = () => {
  const [leaderboard, setLeaderboard] = useState<ReferralUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [claimModalVisible, setClaimModalVisible] = useState(false);
  const [selectedReward, setSelectedReward] = useState<Reward | null>(null);

  // Mock data for demonstration
  const mockLeaderboard: ReferralUser[] = [
    {
      id: '1',
      name: 'Sarah Chen',
      email: 'sarah@example.com',
      totalReferrals: 15,
      successfulReferrals: 12,
      conversionRate: 0.8,
      rank: 1,
      tier: 'platinum',
      rewards: [
        {
          id: '1',
          type: 'ai_credits',
          name: '100 AI Credits',
          description: 'Extra AI strategy generation credits',
          value: 100,
          earnedAt: '2024-12-15T10:30:00Z',
          claimed: false
        },
        {
          id: '2',
          type: 'premium_trial',
          name: '30-Day Pro Trial',
          description: 'Extended Pro tier access',
          value: 30,
          earnedAt: '2024-12-10T14:20:00Z',
          claimed: true
        }
      ]
    },
    {
      id: '2',
      name: 'Mike Rodriguez',
      email: 'mike@example.com',
      totalReferrals: 12,
      successfulReferrals: 9,
      conversionRate: 0.75,
      rank: 2,
      tier: 'gold',
      rewards: [
        {
          id: '3',
          type: 'ai_credits',
          name: '50 AI Credits',
          description: 'Extra AI strategy generation credits',
          value: 50,
          earnedAt: '2024-12-12T09:15:00Z',
          claimed: false
        }
      ]
    },
    {
      id: '3',
      name: 'Emma Thompson',
      email: 'emma@example.com',
      totalReferrals: 8,
      successfulReferrals: 6,
      conversionRate: 0.75,
      rank: 3,
      tier: 'silver',
      rewards: []
    }
  ];

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/referral/leaderboard');
      if (response.ok) {
        const data = await response.json();
        setLeaderboard(data.leaderboard);
      } else {
        // Use mock data as fallback
        setLeaderboard(mockLeaderboard);
      }
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
      setLeaderboard(mockLeaderboard);
    } finally {
      setLoading(false);
    }
  };

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'platinum':
        return <CrownOutlined style={{ color: '#e5e4e2' }} />;
      case 'gold':
        return <TrophyOutlined style={{ color: '#ffd700' }} />;
      case 'silver':
        return <StarOutlined style={{ color: '#c0c0c0' }} />;
      case 'bronze':
        return <FireOutlined style={{ color: '#cd7f32' }} />;
      default:
        return <UserOutlined />;
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'platinum':
        return '#e5e4e2';
      case 'gold':
        return '#ffd700';
      case 'silver':
        return '#c0c0c0';
      case 'bronze':
        return '#cd7f32';
      default:
        return '#d9d9d9';
    }
  };

  const handleClaimReward = async (reward: Reward) => {
    setSelectedReward(reward);
    setClaimModalVisible(true);
  };

  const confirmClaimReward = async () => {
    if (!selectedReward) return;

    try {
      const response = await fetch('/api/referral/claim-reward', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ rewardId: selectedReward.id }),
      });

      if (response.ok) {
        message.success(`Reward claimed successfully: ${selectedReward.name}`);
        
        // Track reward claim
        posthog.capture('referral_reward_claimed', {
          rewardType: selectedReward.type,
          rewardName: selectedReward.name,
          rewardValue: selectedReward.value
        });
        
        // Refresh leaderboard
        fetchLeaderboard();
      } else {
        message.error('Failed to claim reward');
      }
    } catch (error) {
      message.error('Error claiming reward');
    } finally {
      setClaimModalVisible(false);
      setSelectedReward(null);
    }
  };

  const shareReferralLink = () => {
    const referralUrl = `${window.location.origin}/beta?ref=${posthog.get_distinct_id()}`;
    navigator.clipboard.writeText(referralUrl);
    message.success('Referral link copied to clipboard!');
    
    posthog.capture('referral_link_shared', {
      referralUrl
    });
  };

  const columns = [
    {
      title: 'Rank',
      dataIndex: 'rank',
      key: 'rank',
      width: 80,
      render: (rank: number) => {
        if (rank === 1) return <CrownOutlined style={{ color: '#ffd700', fontSize: 20 }} />;
        if (rank === 2) return <TrophyOutlined style={{ color: '#c0c0c0', fontSize: 20 }} />;
        if (rank === 3) return <FireOutlined style={{ color: '#cd7f32', fontSize: 20 }} />;
        return <span style={{ fontWeight: 'bold' }}>{rank}</span>;
      },
    },
    {
      title: 'User',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: ReferralUser) => (
        <Space>
          <Avatar src={record.avatar} icon={<UserOutlined />} />
          <div>
            <div style={{ fontWeight: 'bold' }}>{name}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>{record.email}</div>
          </div>
        </Space>
      ),
    },
    {
      title: 'Tier',
      dataIndex: 'tier',
      key: 'tier',
      width: 100,
      render: (tier: string) => (
        <Tag color={getTierColor(tier)} icon={getTierIcon(tier)}>
          {tier.charAt(0).toUpperCase() + tier.slice(1)}
        </Tag>
      ),
    },
    {
      title: 'Referrals',
      dataIndex: 'totalReferrals',
      key: 'totalReferrals',
      width: 120,
      render: (total: number, record: ReferralUser) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{total}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.successfulReferrals} successful
          </div>
        </div>
      ),
    },
    {
      title: 'Conversion',
      dataIndex: 'conversionRate',
      key: 'conversionRate',
      width: 120,
      render: (rate: number) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{(rate * 100).toFixed(0)}%</div>
          <Progress percent={rate * 100} size="small" showInfo={false} />
        </div>
      ),
    },
    {
      title: 'Rewards',
      dataIndex: 'rewards',
      key: 'rewards',
      render: (rewards: Reward[]) => (
        <Space direction="vertical" size="small">
          {rewards.map((reward) => (
            <div key={reward.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <GiftOutlined style={{ color: reward.claimed ? '#52c41a' : '#1890ff' }} />
              <span style={{ fontSize: '12px' }}>{reward.name}</span>
              {!reward.claimed && (
                <Button 
                  size="small" 
                  type="primary"
                  onClick={() => handleClaimReward(reward)}
                >
                  Claim
                </Button>
              )}
            </div>
          ))}
        </Space>
      ),
    },
  ];

  const currentUser = leaderboard.find(user => user.id === 'current-user-id') || null;

  return (
    <div>
      <Card 
        title={
          <Space>
            <TrophyOutlined />
            <span>Referral Leaderboard</span>
          </Space>
        }
        extra={
          <Button 
            type="primary" 
            icon={<ShareAltOutlined />}
            onClick={shareReferralLink}
          >
            Share Referral Link
          </Button>
        }
      >
        {/* Current User Stats */}
        {currentUser && (
          <Card 
            style={{ marginBottom: 24, background: '#f0f8ff' }}
            size="small"
          >
            <Row gutter={[16, 16]} align="middle">
              <Col span={6}>
                <Statistic
                  title="Your Rank"
                  value={currentUser.rank}
                  suffix={`/ ${leaderboard.length}`}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Total Referrals"
                  value={currentUser.totalReferrals}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Conversion Rate"
                  value={(currentUser.conversionRate * 100).toFixed(1)}
                  suffix="%"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Unclaimed Rewards"
                  value={currentUser.rewards.filter(r => !r.claimed).length}
                  suffix="rewards"
                />
              </Col>
            </Row>
          </Card>
        )}

        {/* Leaderboard Table */}
        <Table
          dataSource={leaderboard}
          columns={columns}
          loading={loading}
          pagination={false}
          rowKey="id"
          rowClassName={(record) => 
            record.id === 'current-user-id' ? 'current-user-row' : ''
          }
        />

        {/* Rewards Info */}
        <Card 
          title="Rewards System" 
          style={{ marginTop: 24 }}
          size="small"
        >
          <Row gutter={[16, 16]}>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="5 Referrals"
                  value="50 AI Credits"
                  prefix={<GiftOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="10 Referrals"
                  value="30-Day Pro Trial"
                  prefix={<GiftOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="15 Referrals"
                  value="Premium Badge"
                  prefix={<GiftOutlined />}
                />
              </Card>
            </Col>
          </Row>
        </Card>
      </Card>

      {/* Claim Reward Modal */}
      <Modal
        title="Claim Reward"
        open={claimModalVisible}
        onOk={confirmClaimReward}
        onCancel={() => {
          setClaimModalVisible(false);
          setSelectedReward(null);
        }}
        okText="Claim Reward"
        cancelText="Cancel"
      >
        {selectedReward && (
          <div>
            <Paragraph>
              <strong>Reward:</strong> {selectedReward.name}
            </Paragraph>
            <Paragraph>
              <strong>Description:</strong> {selectedReward.description}
            </Paragraph>
            <Paragraph>
              <strong>Value:</strong> {selectedReward.value}
            </Paragraph>
            <Paragraph>
              Are you sure you want to claim this reward? It will be added to your account immediately.
            </Paragraph>
          </div>
        )}
      </Modal>

      <style jsx>{`
        .current-user-row {
          background-color: #f0f8ff !important;
        }
      `}</style>
    </div>
  );
};

export default ReferralLeaderboard;
