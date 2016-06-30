import pkg_resources

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import ITemplateProvider

db_version = 1
upgrades = [
    [],
    [ #-- Add the project_milestones table for mapping milestones to projects
      """DROP TABLE IF EXISTS objectlink;""",
      """CREATE TABLE objectlink (
          source_type varchar(64) NOT NULL,
          source_id varchar(64) NOT NULL,
          target_type varchar(64) NOT NULL,
          target_id varchar(64) NOT NULL,
          link_type varchar(32) NOT NULL,
          comment text,
          PRIMARY KEY (source_type, source_id, target_type, target_id, link_type)
      );"""
    ],
]


class EnvironmentSetup(Component):
    implements(IEnvironmentSetupParticipant, ITemplateProvider)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        dbver = self._get_version(db)

        if dbver == db_version:
            return False
        elif dbver > db_version:
            raise TracError(_('Database newer than Object linking version'))
        self.log.info("Object Links schema version is %d, should be %d", dbver, db_version)
        return True

    def upgrade_environment(self, db):
        dbver = self._get_version(db)

        cursor = db.cursor()
        for i in range(dbver + 1, db_version + 1):
            for sql in upgrades[i]:
                cursor.execute(sql)
        cursor.execute("DELETE FROM system WHERE name=%s", ('ObjectLinking',))
        cursor.execute("INSERT INTO system(value, name) VALUES (%s, %s)", (db_version,'ObjectLinking'))
        self.log.info('Upgraded ObjectLinking schema from %d to %d', dbver, db_version)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
       return [('tracprojects', pkg_resources.resource_filename('objectlinking', 'htdocs'))]

    def get_templates_dirs(self):
       return [pkg_resources.resource_filename('objectlinking', 'templates')]


    # internal methods

    def _get_version(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='ObjectLinking'")
        row = cursor.fetchone()
        if row:
            return int(row[0])
        else:
            return 0

  