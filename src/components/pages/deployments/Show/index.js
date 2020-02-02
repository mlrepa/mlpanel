import React from "react";
import {
  Show,
  SimpleShowLayout,
  TopToolbar,
  ListButton,
  TextField,
  DeleteButton,
  DateField,
  UrlField
} from "react-admin";
import Button from "@material-ui/core/Button";

const DeploymentTitle = ({ record }) => {
  return <span>{`Experiment ${record ? `"${record.name}"` : ""}`}</span>;
};

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

const DeploymentShowActions = ({ basePath, data, resource }) => (
  <TopToolbar>
    <DeployPutButton record={data} />
    <ListButton style={{ marginLeft: 20 }} basePath={basePath} />
    <DeleteButton basePath={basePath} record={data} resource={resource} />
  </TopToolbar>
);

const DeploymentShow = props => (
  <Show
    actions={<DeploymentShowActions />}
    title={<DeploymentTitle />}
    {...props}
  >
    <SimpleShowLayout>
      <TextField source="id" />
      <TextField source="project_id" />
      <TextField source="model_id" />
      <TextField source="version" />
      <UrlField source="model_uri" />
      <TextField source="type" />
      <DateField source="created_at" />
      <TextField source="status" />
      <TextField source="host" />
      <TextField source="port" />
    </SimpleShowLayout>
  </Show>
);

export default DeploymentShow;
