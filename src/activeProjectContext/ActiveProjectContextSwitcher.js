import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import Select from '@material-ui/core/Select';
import MenuItem from '@material-ui/core/MenuItem';
import { setActiveProject as setActiveProjectAction } from './activeProjectContext';


class ProjectSelector extends Component {
    
    componentDidMount() {
        const activeProjectId = ProjectSelector.getActiveProjectIdFromURL() || 0;
        console.log({ activeProjectId });
        this.props.setActiveProject(activeProjectId);
    }
    
    handleChange = (event) => {
        const activeProjectId = event.target.value;
        ProjectSelector.setActiveProjectIdToURL(activeProjectId);
        this.props.setActiveProject(activeProjectId);
    }

    render() {
        return (
            <Select value={this.props.activeProjectId} onChange={this.handleChange}>
                <MenuItem value={0}>Project 0</MenuItem>
                <MenuItem value={1}>Project 1</MenuItem>
                <MenuItem value={2}>Project 2</MenuItem>
            </Select>
        )
    }

    static setActiveProjectIdToURL(activeProjectId) {
        const url = new URL(window.location.href);
        url.searchParams.set('active_project_id', activeProjectId);
        window.history.pushState(null, '', url.toString());
    }

    static getActiveProjectIdFromURL() {
        const url = new URL(window.location.href);
        return url.searchParams.get('active_project_id');
    }
}

ProjectSelector.propTypes = {
    setActiveProject: PropTypes.func,
    record: PropTypes.object,
};

export default connect((state) => ({
    activeProjectId: state.activeProject,
}), {
    setActiveProject: setActiveProjectAction,
})(ProjectSelector);