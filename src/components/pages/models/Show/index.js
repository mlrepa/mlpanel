import React from "react";
import {
  Show,
  SimpleShowLayout,
  TopToolbar,
  ListButton,
  TextField,
  DeleteButton
} from "react-admin";

import FormattedDateField from "../../../shared/FormattedDateField";

const ModelTitle = ({ record }) => {
  return <span>{`Model ${record ? `"${record.id}"` : ""}`}</span>;
};

const ModelShowActions = ({ basePath, data, resource }) => (
  <TopToolbar>
    <ListButton basePath={basePath} />
    <DeleteButton basePath={basePath} record={data} resource={resource} />
  </TopToolbar>
);

const ModelShow = props => (
  <Show actions={<ModelShowActions />} title={<ModelTitle />} {...props}>
    <SimpleShowLayout>
      <TextField source="id" />
      <FormattedDateField source="creation_timestamp" />
      <FormattedDateField source="last_updated_timestamp" />
    </SimpleShowLayout>
  </Show>
);

export default ModelShow;
