import React from 'react'
import { Link } from 'react-router-dom'
import { Layout, Menu, Dropdown, Button, Space } from 'antd'
import { UserOutlined, ShoppingCartOutlined, MenuOutlined } from '@ant-design/icons'

const { Header } = Layout

const HeaderComp = () => {
  const user = null // 这里应该从全局状态获取用户信息

  const userMenuItems = [
    {
      key: 'profile',
      label: <Link to="/profile">个人中心</Link>
    },
    {
      key: 'orders',
      label: <Link to="/orders">我的订单</Link>
    },
    {
      key: 'logout',
      label: '退出登录'
    }
  ]

  return (
    <Header>
      <div className="logo">FastAPI Shop</div>
      <Menu
        theme="dark"
        mode="horizontal"
        defaultSelectedKeys={['1']}
        items={[
          {
            key: '1',
            label: <Link to="/">首页</Link>
          },
          {
            key: '2',
            label: <Link to="/products">商品</Link>
          }
        ]}
        style={{ flex: 1, minWidth: 0 }}
      />
      <Space>
        <Link to="/cart">
          <Button type="text" icon={<ShoppingCartOutlined />} style={{ color: 'white' }}>
            购物车
          </Button>
        </Link>
        {user ? (
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Button type="text" icon={<UserOutlined />} style={{ color: 'white' }}>
              {user.username}
            </Button>
          </Dropdown>
        ) : (
          <Link to="/login">
            <Button type="primary">登录</Button>
          </Link>
        )}
      </Space>
    </Header>
  )
}

export default HeaderComp