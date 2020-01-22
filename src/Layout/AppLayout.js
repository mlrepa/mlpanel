import React from 'react'
import { Layout } from 'react-admin';
import CustomflowBar from '../CustoflowBar/CustomflowBar';

const AppLayout = (props) => <Layout {...props} appBar={CustomflowBar} />;

export default AppLayout;