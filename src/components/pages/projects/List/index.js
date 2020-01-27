import React from "react";
import { List, Datagrid, TextField, ShowButton, DateField } from "react-admin";

const ProjectList = props => {
  return (
    <List bulkActionButtons={false} {...props}>
      <Datagrid>
        <TextField source="id" />
        <TextField source="name" />
        <TextField source="status" />
        <TextField source="description" />
        <DateField source="createdAt" />
        <ShowButton />
      </Datagrid>
    </List>
  );
};

export default ProjectList;
