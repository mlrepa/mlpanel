import React from "react";
import { List, Datagrid, TextField, ShowButton, DateField } from "react-admin";
import Button from "@material-ui/core/Button";

const DeployPutButton = ({ record }) => {
  const handleDeploy = () => {
    fetch(
      `http://35.227.124.46:8080/deployments/${record.id}/${
        record.status === "running" ? "stop" : "run"
      }`,
      {
        method: "PUT"
      }
    )
      .then(r => r.json())
      .then(res => {
        alert(res.message || "Ok");
      })
      .catch(err => alert(err));
  };
  return (
    <Button variant="contained" color="primary" onClick={() => handleDeploy()}>
      {record.status === "running" ? "stop" : "run"}
    </Button>
  );
};

const DeploymentList = props => {
  const { dispatch, ...restProps } = props;

  return (
    <List {...restProps} bulkActionButtons={false}>
      <Datagrid>
        <TextField source="id" />
        <TextField source="project_id" />
        <TextField source="model_id" />
        <TextField source="version" />
        <DateField source="created_at" />
        <TextField source="status" />
        <TextField source="type" />
        <ShowButton />
        <DeployPutButton />
      </Datagrid>
    </List>
  );
};

export default DeploymentList;
