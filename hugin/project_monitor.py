
import os
import glob
import datetime
import scilifelab.illumina as illumina
from scilifelab.illumina.hiseq import HiSeqSampleSheet
from scilifelab.bcbio.qc import RunInfoParser
from hugin.trello_utils import TrelloUtils
    
RUN_PROCESS_STEPS = ["bcbb analysis started",
                     "bcbb analysis completed",
                     "sample qualities evaluated",
                     "sample species confirmed by blast",
                     "customer uppnex id verified",
                     "raw data delivered to customer inbox",
                     "sample status note generated",
                     "project status note generated",
                     "delivery notes copied to customer inbox",
                     "delivery email sent to customer and application specialists",
                     "delivery marked in Genomics Project List"
                     ]

BEST_PRACTICE_ANALYSIS_STEPS = ["data from sample runs merged",
                                 "best practice analysis started",
                                 "best practice analysis completed",
                                 "best practice analysis results delivered to customer inbox",
                                 "best practice analysis report generated",
                                 "best practice analysis report copied to customer inbox",
                                 "best practice analysis delivery marked in Genomics Project List"
                                 ]

PROJECT_COMPLETION_STEPS = ["all raw data delivered",
                            "all raw data delivered marked in Genomics Project List",
                            "best practice analysis delivered",
                            "project finished"]

SEQUENCING_IN_PROGRESS = "Sequencing"
BCBB_ANALYSIS_IN_PROGRESS = "bcbb analysis"
BP_AND_DELIVERY_IN_PROGRESS = "Best practice and delivery"
PROJECT_FINISHED = "Finished"

class ProjectMonitor(object):
    
    def __init__(self, config):
        self.trello = TrelloUtils(config)
        self.trello_board = self.trello.get_board(config.get("trello",{}).get("project_tracking_board",None),True)
        assert self.trello_board is not None, "Could not locate project tracking board in Trello"
        self.archive_folders = [d.strip() for d in config.get("archive_folders","").split(",")]
        self.analysis_folders = [d.strip() for d in config.get("analysis_folders","").split(",")]
        self.config = config
        
    def add_project_card(self, project, status=SEQUENCING_IN_PROGRESS):
        """Add a project card"""
        
        card = self.trello.get_card_on_board(self.trello_board, project)
        lst = self.trello.add_list(self.trello_board, status)
        if card is None:
            desc = self.get_project_metadata(project)
            card = self.trello.add_card(lst,project,desc)
            card.add_checklist("Project", PROJECT_COMPLETION_STEPS)
            card.add_checklist("Best practice analysis", BEST_PRACTICE_ANALYSIS_STEPS)
        
        card.set_closed(False)
        card.change_list(lst.id)
        return card
    
    def add_run_to_project(self, project, run):
        """Add a run to a project card
        """
        
        card = self.add_project_card(project)
        # Fetch the checklists on this card
        card.fetch()
        if run['name'] not in [chklst.name for chklst in card.checklists]:
            card.add_checklist(run['name'], RUN_PROCESS_STEPS)
        
        # Make sure to uncheck any incompatible completed events
        for chklst in card.checklists:
            if chklst.name in ["Project","Best practice analysis"]:
                for item in chklst.items:
                    chklst.set_checklist_item(item.get('name',''),False)

        
    def get_project_metadata(self, project):
        return ""