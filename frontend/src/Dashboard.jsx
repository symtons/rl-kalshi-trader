import React, { useState, useEffect } from 'react';
import { 
  Container, Grid, Paper, Typography, Box, Card, CardContent,
  Table, TableBody, TableCell, TableHead, TableRow, Chip
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

function Dashboard() {
  const [portfolio, setPortfolio] = useState({
    balance: 0,
    pnl: 0,
    total_trades: 0,
    win_rate: 0
  });
  
  const [trades, setTrades] = useState([]);
  const [portfolioHistory, setPortfolioHistory] = useState([]);
  const [latestDecision, setLatestDecision] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const portfolioRes = await axios.get(API_URL + '/portfolio');
      const tradesRes = await axios.get(API_URL + '/trades');
      const historyRes = await axios.get(API_URL + '/portfolio-history');
      const decisionRes = await axios.get(API_URL + '/latest-decision');

      setPortfolio(portfolioRes.data);
      setTrades(tradesRes.data);
      setPortfolioHistory(historyRes.data);
      setLatestDecision(decisionRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Typography variant="h4">Loading dashboard...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom sx={{ fontWeight: 'bold', mb: 4 }}>
        🤖 RL Trading Bot Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#1e1e1e', color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <AccountBalanceWalletIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Balance</Typography>
              </Box>
              <Typography variant="h4">{'$' + portfolio.balance.toFixed(2)}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: portfolio.pnl >= 0 ? '#1b5e20' : '#b71c1c', color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                {portfolio.pnl >= 0 ? <TrendingUpIcon /> : <TrendingDownIcon />}
                <Typography variant="h6" sx={{ ml: 1 }}>P&L</Typography>
              </Box>
              <Typography variant="h4">
                {portfolio.pnl >= 0 ? '+$' : '-$'}{Math.abs(portfolio.pnl).toFixed(2)}
              </Typography>
              <Typography variant="body2">
                ({((portfolio.pnl / 10000) * 100).toFixed(2)}%)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#0d47a1', color: 'white' }}>
            <CardContent>
              <Typography variant="h6">Total Trades</Typography>
              <Typography variant="h4">{portfolio.total_trades}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#4a148c', color: 'white' }}>
            <CardContent>
              <Typography variant="h6">Win Rate</Typography>
              <Typography variant="h4">{portfolio.win_rate.toFixed(1)}%</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {latestDecision && (
        <Paper sx={{ p: 3, mb: 4, bgcolor: '#f5f5f5' }}>
          <Typography variant="h5" gutterBottom>🎯 Latest Agent Decision</Typography>
          <Box display="flex" alignItems="center" gap={2}>
            <Chip 
              label={latestDecision.action} 
              color={latestDecision.action && latestDecision.action.includes('BUY') ? 'success' : latestDecision.action === 'HOLD' ? 'default' : 'error'}
              sx={{ fontSize: '1.2rem', py: 2, px: 1 }}
            />
            <Typography variant="h6">
              Size: {latestDecision.size} contracts
            </Typography>
          </Box>
        </Paper>
      )}

      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>📈 Portfolio Value Over Time</Typography>
        {portfolioHistory.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={portfolioHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="step" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#1976d2" strokeWidth={2} name="Portfolio Value" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <Typography>No data yet - start trading bot to see chart</Typography>
        )}
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>📊 Recent Trades</Typography>
        {trades.length > 0 ? (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Time</strong></TableCell>
                <TableCell><strong>Market</strong></TableCell>
                <TableCell><strong>Action</strong></TableCell>
                <TableCell><strong>Side</strong></TableCell>
                <TableCell><strong>Size</strong></TableCell>
                <TableCell><strong>Price</strong></TableCell>
                <TableCell><strong>Cost</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {trades.map((trade, idx) => (
                <TableRow key={idx}>
                  <TableCell>{trade.timestamp}</TableCell>
                  <TableCell>{trade.ticker}</TableCell>
                  <TableCell>
                    <Chip 
                      label={trade.action ? trade.action.toUpperCase() : 'N/A'} 
                      size="small"
                      color={trade.action === 'buy' ? 'success' : 'warning'}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={trade.side ? trade.side.toUpperCase() : 'N/A'} 
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{trade.size}</TableCell>
                  <TableCell>{trade.price}¢</TableCell>
                  <TableCell>{'$' + trade.cost.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <Typography>No trades yet - start trading bot to see trades</Typography>
        )}
      </Paper>
    </Container>
  );
}

export default Dashboard;
