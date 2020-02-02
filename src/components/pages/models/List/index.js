import React from "react";
import { connect } from "react-redux";
import { List, Datagrid, TextField, ShowButton } from "react-admin";
import Button from "@material-ui/core/Button";

import FormattedDateField from "../../../shared/FormattedDateField";
import { stringify } from "query-string";

const VersionField = ({ record }) => {
  const [modelVersions, setModelVersions] = React.useState([]);
  React.useEffect(() => {
    const currentEntities = JSON.parse(
      localStorage.getItem("current_entities")
    );
    fetch(
      `http://35.227.124.46:8080/model-versions?${stringify(
        currentEntities
      )}&model_id=${record.id}`,
      {
        method: "GET"
      }
    )
      .then(r => r.json())
      .then(res => {
        setModelVersions(res);
      })
      .catch(err => console.log(err));
  }, []);
  return (
    <TextField
      source="version"
      record={modelVersions[modelVersions.length - 1]}
      basePath="/registered-models"
      resource="/registered-models"
    />
  );
};

const DeployButton = ({ record }) => {
  const [modelVersions, setModelVersions] = React.useState([]);
  React.useEffect(() => {
    const currentEntities = JSON.parse(
      localStorage.getItem("current_entities")
    );
    fetch(
      `http://35.227.124.46:8080/model-versions?${stringify(
        currentEntities
      )}&model_id=${record.id}`,
      {
        method: "GET"
      }
    )
      .then(r => r.json())
      .then(res => {
        setModelVersions(res);
      })
      .catch(err => console.log(err));
  }, []);

  const handleDeploy = () => {
    const currentEntities = JSON.parse(
      localStorage.getItem("current_entities")
    );
    fetch(
      `http://35.227.124.46:8080/deployments?${stringify(
        currentEntities
      )}&version=${modelVersions[modelVersions.length - 1].version}&model_id=${
        record.id
      }&type=local`,
      {
        method: "POST"
      }
    )
      .then(r => r.json())
      .then(res => {
        alert(res.message);
      })
      .catch(err => alert(err));
  };
  return (
    <Button variant="contained" color="primary" onClick={() => handleDeploy()}>
      Deploy
    </Button>
  );
};

const ModelList = props => {
  const { activeProjectId, dispatch, ...restProps } = props;

  return (
    <List
      {...restProps}
      bulkActionButtons={false}
      filter={{ project_id: activeProjectId }}
    >
      <Datagrid>
        <TextField source="id" />
        <FormattedDateField source="creation_timestamp" />
        <FormattedDateField source="last_updated_timestamp" />
        <VersionField source="version" />
        <ShowButton />
        <DeployButton />
      </Datagrid>
    </List>
  );
};

export default connect(state => ({
  activeProjectId: state.activeProject
}))(ModelList);
