import React from "react";
import { List, Datagrid, TextField, EmailField } from "react-admin";

export const UserList = props => (
  <List {...props}>
    <Datagrid rowClick="edit">
      <TextField source="id" />
      <TextField source="name" />
      <TextField source="username" />
      <EmailField source="email" />
      <TextField source="address.street" />
      <TextField source="phone" />
      <TextField source="company.name" />
    </Datagrid>
  </List>
);
