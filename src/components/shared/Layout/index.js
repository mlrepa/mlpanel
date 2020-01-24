import React from "react";
import { Layout } from "react-admin";
import CustomFlowBar from "../CustomFlowBar";

const LayoutComponent = props => <Layout {...props} appBar={CustomFlowBar} />;

export default LayoutComponent;
