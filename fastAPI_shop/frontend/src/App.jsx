import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'
import Header from './components/Header'
import Footer from './components/Footer'
import Home from './views/Home'
import Login from './views/Login'
import Register from './views/Register'
import ProductList from './views/ProductList'
import ProductDetail from './views/ProductDetail'
import Cart from './views/Cart'
import Checkout from './views/Checkout'
import OrderList from './views/OrderList'
import Profile from './views/Profile'
import './App.css'

const { Content } = Layout

function App() {
  return (
    <Layout className="layout">
      <Header />
      <Content style={{ padding: '0 50px' }}>
        <div className="site-layout-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/products" element={<ProductList />} />
            <Route path="/products/:id" element={<ProductDetail />} />
            <Route path="/cart" element={<Cart />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/orders" element={<OrderList />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </div>
      </Content>
      <Footer />
    </Layout>
  )
}

export default App