def get_routes(repository, revision, hg_push_id):
    treeherder_top_route_routes = ('tc-treeherder', 'tc-treeherder-stage',)
    return [
        '{top_route}.v2.{repository}.{revision}.{hg_push_id}'.format(
            top_route=top_route, repository=repository,
            revision=revision, hg_push_id=hg_push_id
        )
        for top_route in treeherder_top_route_routes
    ]
