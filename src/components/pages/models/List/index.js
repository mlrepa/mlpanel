import React from "react";
import { connect } from "react-redux";
import { List, Datagrid, TextField, ShowButton } from "react-admin";

import FormattedDateField from "../../../shared/FormattedDateField";

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
        <ShowButton />
      </Datagrid>
    </List>
  );
};

export default connect(state => ({
  activeProjectId: state.activeProject
}))(ModelList);
