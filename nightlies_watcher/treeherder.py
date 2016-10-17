from nightlies_watcher.hg_mozilla import get_minimal_repository_name


def get_routes(repository, revision, hg_push_id):
    treeherder_top_route_routes = ('tc-treeherder', 'tc-treeherder-stage',)
    return [
        '{top_route}.v2.{minimal_repo_name}.{revision}.{hg_push_id}'.format(
            top_route=top_route, minimal_repo_name=get_minimal_repository_name(repository),
            revision=revision, hg_push_id=hg_push_id
        )
        for top_route in treeherder_top_route_routes
    ]
