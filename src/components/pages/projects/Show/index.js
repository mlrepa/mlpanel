import React from "react";
import {
  TextField,
  Show,
  SimpleShowLayout,
  DateField,
  UrlField,
  TopToolbar,
  ListButton,
  DeleteButton,
  showNotification
} from "react-admin";
import Button from "@material-ui/core/Button";
import Axios from "axios";

import IFrame from "../IFrame";

const ProjectTitle = ({ record }) => {
  return <span>Project {record ? `"${record.id}"` : ""}</span>;
};

const ProjectShowActions = ({ basePath, data, resource }) => {
  const handleProjectAction = type => {
    Axios.put(`http://35.227.124.46:8080/${resource}/${data.id}/${type}`).then(
      res => {
        console.log(res);
        alert(`${resource} ${type} status: OK`);
      }
    );
  };

  return (
    <TopToolbar>
      <ListButton className="button" basePath={basePath} />
      <DeleteButton
        className="button"
        basePath={basePath}
        record={data}
        resource={resource}
      />
      <Button
        className="button"
        variant="outlined"
        onClick={() => handleProjectAction("run")}
      >
        Run
      </Button>
      <Button
        className="button"
        variant="outlined"
        onClick={() => handleProjectAction("terminate")}
      >
        Terminate
      </Button>
      <Button
        className="button"
        variant="outlined"
        onClick={() => handleProjectAction("archive")}
      >
        Archive
      </Button>
      <Button variant="outlined" onClick={() => handleProjectAction("restore")}>
        Restore
      </Button>
    </TopToolbar>
  );
};

const ProjectShow = props => (
  <div>
    <Show actions={<ProjectShowActions />} title={<ProjectTitle />} {...props}>
      <SimpleShowLayout>
        <TextField source="id" />
        <TextField source="name" />
        <DateField source="createdAt" />
        <TextField source="status" />
        <TextField source="description" />
        <TextField source="path" />
        <UrlField source="mlflowUri" />
        <IFrame {...props} />
      </SimpleShowLayout>
    </Show>
  </div>
);

export default ProjectShow;
