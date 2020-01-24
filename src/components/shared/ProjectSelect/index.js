import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { withRouter } from "react-router";
import { parse } from "query-string";

import Select from "@material-ui/core/Select";
import MenuItem from "@material-ui/core/MenuItem";

import { setActiveProject as setActiveProjectAction } from "../../../context/entities/projectContext";

class ProjectSelect extends Component {
  state = {
    projects: []
  };

  getProjectList = () => {
    fetch(`http://35.227.124.46:8080/projects`, { method: "GET" })
      .then(r => r.json())
      .then(res =>
        this.setState({
          projects: res
        })
      );
  };

  componentDidMount() {
    const {
      props: {
        setActiveProject,
        history,
        location: { pathname, search }
      },
      getProjectList
    } = this;

    const { current_project } = parse(search);

    history.push(`${pathname}?current_project=${current_project || 1}`);

    getProjectList();
    setActiveProject(current_project || 1);
  }

  handleChange = event => {
    const {
      props: {
        setActiveProject,
        history,
        location: { pathname }
      }
    } = this;

    const activeProjectId = event.target.value;

    history.push(`${pathname}?current_project=${activeProjectId}`);
    setActiveProject(activeProjectId);
  };

  render() {
    const {
      props: { activeProjectId },
      state: { projects }
    } = this;

    return (
      <Select value={activeProjectId} onChange={this.handleChange}>
        {projects &&
          projects.map(item => (
            <MenuItem key={item.id} value={item.id}>
              {`Project ${item.id}`}
            </MenuItem>
          ))}
      </Select>
    );
  }
}

ProjectSelect.propTypes = {
  setActiveProject: PropTypes.func
};

const mapStateToProps = state => ({
  activeProjectId: state.activeProject
});

const mapDispatchToProps = dispatch => ({
  setActiveProject: projectId => dispatch(setActiveProjectAction(projectId))
});

export default withRouter(
  connect(
    mapStateToProps,
    mapDispatchToProps
  )(ProjectSelect)
);
